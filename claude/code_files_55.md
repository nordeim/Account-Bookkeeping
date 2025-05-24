<think>
The application is still launching and shutting down cleanly. The `FiscalYearDialog` has been defined.
Now, we need to integrate this into `app/ui/settings/settings_widget.py` and ensure the backend (`FiscalPeriodManager` and `FiscalYearService`) can handle the creation of fiscal years and their periods.

**Plan for This Step (Phase 1.1.3 of MVP Step 1):**

1.  **Enhance `app/ui/settings/settings_widget.py`**:
    *   **Import `FiscalYearDialog`** and the new `FiscalYearData` DTO (for displaying).
    *   **Add UI Elements for Fiscal Year Management**:
        *   A `QGroupBox` titled "Fiscal Year Management".
        *   A `QTableView` (or `QListWidget` for simplicity initially) to display existing fiscal years. We'll need a simple model for this table if using `QTableView`.
        *   Columns: "Year Name", "Start Date", "End Date", "Status (Open/Closed)".
        *   Buttons: "Add New Fiscal Year...", "Manage Periods..." (stub for now), "Close Year" (stub for now).
    *   **`load_settings()` enhancement**:
        *   This async method (already called via `schedule_task_from_qt`) will now also fetch existing fiscal years using `app_core.fiscal_period_manager.get_all_fiscal_years()`.
        *   The fetched data will be used to populate the fiscal year list/table via `QMetaObject.invokeMethod` calling a new slot.
    *   **"Add New Fiscal Year..." Button Logic**:
        *   Create and `exec_()` an instance of `FiscalYearDialog`.
        *   If the dialog is accepted, get the `FiscalYearCreateData` DTO.
        *   Schedule an async task (`schedule_task_from_qt`) to call `app_core.fiscal_period_manager.create_fiscal_year(dto)`.
        *   On successful creation, refresh the list of fiscal years in the UI.
        *   Display success/error messages using `QMessageBox` (via `QMetaObject.invokeMethod` if called from async task callback).

2.  **Enhance `app/accounting/fiscal_period_manager.py` (Review/Refine)**:
    *   `create_fiscal_year(fy_data: FiscalYearCreateData)`:
        *   Ensure it uses `self.fiscal_year_service.get_by_name()` and `self.fiscal_year_service.get_by_date_overlap(exclude_id=None)` for validation.
        *   After saving the `FiscalYear`, if `fy_data.auto_generate_periods` is set, call `self.generate_periods_for_year()`.
    *   `generate_periods_for_year(fiscal_year: FiscalYear, period_type: str, user_id: int)`:
        *   Double-check date logic for period boundaries (e.g., handling of month ends for `relativedelta`).
        *   Ensure `is_adjustment` is set to `False` for normally generated periods.

3.  **Ensure `app/services/accounting_services.py` (`FiscalYearService`) is complete for these operations**:
    *   `get_all()`: Returns `List[FiscalYear]`.
    *   `get_by_name(name: str)`: Returns `Optional[FiscalYear]`.
    *   `get_by_date_overlap(start: date, end: date, exclude_id: Optional[int] = None)`: Returns `Optional[FiscalYear]`.
    *   `save(entity: FiscalYear)`: Saves new or updates existing.

**File Generation Order:**
I'll first update `app/ui/settings/settings_widget.py` as it's the main UI driver for this feature. This will involve creating stubs or defining how it interacts with the new dialog and manager methods. Then, I'll ensure `FiscalPeriodManager` and `FiscalYearService` methods are robust.

The `FiscalYearDialog` was provided in the previous step.
Let's start with `app/ui/settings/settings_widget.py`.
</think>

It's excellent that the application remains stable! We can now proceed with integrating the fiscal year management UI.

This involves:
1.  Updating `app/ui/settings/settings_widget.py` to include a section for displaying fiscal years and a button to launch the `FiscalYearDialog`.
2.  Implementing the logic to load existing fiscal years and handle the creation of new ones via the dialog and `FiscalPeriodManager`.
3.  Ensuring `FiscalPeriodManager` and `FiscalYearService` are robust for these operations. The `FiscalYearService` was updated in the previous step. I will now focus on ensuring `FiscalPeriodManager` logic is correct and then updating `SettingsWidget`.

---
**1. Review and Enhance `app/accounting/fiscal_period_manager.py`**
Let's ensure the manager methods for creating fiscal years and generating periods are robust.

```python
# File: app/accounting/fiscal_period_manager.py
from typing import List, Optional, TYPE_CHECKING, cast
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result
from app.utils.pydantic_models import FiscalYearCreateData # DTO for creation
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 


class FiscalPeriodManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service 
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service 
        
    async def create_fiscal_year_and_periods(self, fy_data: FiscalYearCreateData) -> Result[FiscalYear]:
        """
        Creates a fiscal year and, if requested, generates its accounting periods.
        This is a single transactional operation (conceptually).
        """
        if fy_data.start_date >= fy_data.end_date:
            return Result.failure(["Fiscal year start date must be before end date."])

        existing_by_name = await self.fiscal_year_service.get_by_name(fy_data.year_name)
        if existing_by_name:
            return Result.failure([f"A fiscal year with the name '{fy_data.year_name}' already exists."])

        overlapping_fy = await self.fiscal_year_service.get_by_date_overlap(fy_data.start_date, fy_data.end_date)
        if overlapping_fy:
            return Result.failure([f"The proposed date range overlaps with existing fiscal year '{overlapping_fy.year_name}' ({overlapping_fy.start_date} - {overlapping_fy.end_date})."])

        # Use a single session for all database operations in this method
        async with self.app_core.db_manager.session() as session: # type: ignore
            # Create FiscalYear ORM object
            fy = FiscalYear(
                year_name=fy_data.year_name, 
                start_date=fy_data.start_date, 
                end_date=fy_data.end_date, 
                created_by_user_id=fy_data.user_id, 
                updated_by_user_id=fy_data.user_id,
                is_closed=False 
            )
            session.add(fy)
            await session.flush() # Get ID for fy
            await session.refresh(fy) # Refresh to get all defaults and ID

            if fy_data.auto_generate_periods and fy_data.auto_generate_periods in ["Month", "Quarter"]:
                period_generation_result = await self._generate_periods_for_year_internal(
                    fy, fy_data.auto_generate_periods, fy_data.user_id, session
                )
                if not period_generation_result.is_success:
                    await session.rollback() # Rollback FY creation if period generation fails
                    error_msg = f"Failed to generate periods for '{fy.year_name}': {', '.join(period_generation_result.errors)}"
                    return Result.failure([error_msg])
            
            # If we reach here, all operations within this session are successful
            # The session will commit automatically when the 'async with' block exits without error.
            return Result.success(fy)
        
        # Fallback in case of unexpected exit from try (should not happen if exceptions are caught)
        # This path might be hit if an exception occurs outside the try-block for session management.
        return Result.failure(["An unexpected error occurred during fiscal year creation."])


    async def _generate_periods_for_year_internal(self, fiscal_year: FiscalYear, period_type: str, user_id: int, session: Any) -> Result[List[FiscalPeriod]]:
        """
        Internal helper to generate periods within an existing session.
        `session` is an active SQLAlchemy AsyncSession.
        """
        if not fiscal_year or not fiscal_year.id:
            return Result.failure(["Valid FiscalYear object with an ID must be provided."])
        
        # Check if periods already exist for this year and type (using the provided session)
        stmt_existing = select(FiscalPeriod).where(
            FiscalPeriod.fiscal_year_id == fiscal_year.id,
            FiscalPeriod.period_type == period_type
        )
        existing_periods_result = await session.execute(stmt_existing)
        if existing_periods_result.scalars().first():
             return Result.failure([f"{period_type} periods already exist for fiscal year '{fiscal_year.year_name}'."])


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
                # For quarters, advance 3 months from start, then find end of that 3rd month
                # Example: if current_start_date is Jan 15. Quarter 1 is Jan-Mar.
                # month_in_quarter = (current_start_date.month - 1) % 3 # 0 for Jan,Apr,Jul,Oct; 1 for Feb,May,Aug,Nov etc.
                # months_to_add_for_quarter_end = 2 - month_in_quarter
                # quarter_end_month_start = current_start_date + relativedelta(months=months_to_add_for_quarter_end, day=1)
                # current_end_date = quarter_end_month_start + relativedelta(months=1) - relativedelta(days=1)
                
                # Simpler: advance by 2 months, then find end of that month (effectively 3 month period)
                # This gives calendar-aligned quarters if FY starts on a quarter boundary.
                # For more precise quarter definitions based on FY start, logic can be more complex.
                # Current logic: creates periods like Jan-Mar, Apr-Jun etc. relative to current_start_date.
                month_end_of_third_month = current_start_date + relativedelta(months=2, day=1) + relativedelta(months=1) - relativedelta(days=1)
                current_end_date = month_end_of_third_month

                if current_end_date > fy_end_date: current_end_date = fy_end_date
                period_name = f"Q{period_number} {fiscal_year.year_name}"
            else: 
                return Result.failure(["Invalid period type during generation."]) # Should be caught earlier

            fp = FiscalPeriod(
                fiscal_year_id=fiscal_year.id, name=period_name,
                start_date=current_start_date, end_date=current_end_date,
                period_type=period_type, status="Open", period_number=period_number,
                is_adjustment=False,
                created_by_user_id=user_id, updated_by_user_id=user_id
            )
            session.add(fp) # Add to session, commit will happen at the end of create_fiscal_year_and_periods
            periods.append(fp)

            if current_end_date >= fy_end_date: break 
            current_start_date = current_end_date + relativedelta(days=1)
            period_number += 1
        
        # Flush to ensure periods are persisted if needed for subsequent operations within the same transaction
        await session.flush()
        for p in periods: # Refresh to get IDs and defaults if any
            await session.refresh(p)
            
        return Result.success(periods)

    # Keep other methods like close_period, reopen_period, get_current_fiscal_period, 
    # get_all_fiscal_years, get_fiscal_year_by_id, get_periods_for_fiscal_year, close_fiscal_year
    # as they were in the previous version, ensuring they use self.fiscal_year_service
    # and self.fiscal_period_service correctly.

    async def close_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Closed': return Result.failure(["Period is already closed."])
        if period.status == 'Archived': return Result.failure(["Cannot close an archived period."])
        
        period.status = 'Closed'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period) # Assumes service has update
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
        updated_period = await self.fiscal_period_service.update(period) # Assumes service has update
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
        fy.updated_by_user_id = user_id # UserAuditMixin on FiscalYear handled by ORM/service
        
        try:
            updated_fy = await self.fiscal_year_service.save(fy)
            return Result.success(updated_fy)
        except Exception as e:
            return Result.failure([f"Error closing fiscal year: {str(e)}"])

```

**Validation of `app/accounting/fiscal_period_manager.py` Changes:**
*   Renamed `create_fiscal_year` to `create_fiscal_year_and_periods` for clarity and made it accept `FiscalYearCreateData`.
*   This method now uses a single database session (transaction) for creating the fiscal year and its periods, ensuring atomicity. If period generation fails, the fiscal year creation is rolled back.
*   Validation for year name conflict and date overlap is performed using `FiscalYearService`.
*   `_generate_periods_for_year_internal` is a new helper method that takes an active session.
*   Logic for calculating monthly and quarterly period end dates within `_generate_periods_for_year_internal` has been refined.
*   Audit fields (`created_by_user_id`, `updated_by_user_id`) are correctly passed from the DTO/`user_id` argument.
*   Added `get_all_fiscal_years`, `get_fiscal_year_by_id`, `get_periods_for_fiscal_year` methods to be called by the UI.
*   Added `close_fiscal_year` method stub with basic checks.

---
Next, I will create the new file `app/ui/accounting/fiscal_year_dialog.py`.
