# File: app/accounting/fiscal_period_manager.py
# (Content as previously generated, verified - now app_core.fiscal_year_service should be available)
from typing import List, Optional, TYPE_CHECKING # Add TYPE_CHECKING
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService # Will be available via app_core
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting


class FiscalPeriodManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service 
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service 
        
    async def create_fiscal_year(self, year_name: str, start_date: date, end_date: date, user_id: int) -> Result[FiscalYear]:
        if start_date >= end_date:
            return Result.failure(["Start date must be before end date."])
        
        existing_fy_overlap = await self.fiscal_year_service.get_by_date_overlap(start_date, end_date)
        if existing_fy_overlap:
            return Result.failure([f"Fiscal year dates overlap with existing year '{existing_fy_overlap.year_name}'."])
        
        existing_fy_name = await self.fiscal_year_service.get_by_name(year_name)
        if existing_fy_name:
             return Result.failure([f"Fiscal year name '{year_name}' already exists."])


        fy = FiscalYear(
            year_name=year_name, start_date=start_date, end_date=end_date, 
            created_by_user_id=user_id, updated_by_user_id=user_id
        )
        saved_fy = await self.fiscal_year_service.save(fy) 
        return Result.success(saved_fy)

    async def generate_periods_for_year(self, fiscal_year: FiscalYear, period_type: str, user_id: int) -> Result[List[FiscalPeriod]]:
        if period_type not in ["Month", "Quarter"]:
            return Result.failure(["Invalid period type. Must be 'Month' or 'Quarter'."])

        existing_periods = await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year.id, period_type)
        if existing_periods:
            return Result.failure([f"{period_type} periods already exist for fiscal year '{fiscal_year.year_name}'."])

        periods: List[FiscalPeriod] = []
        current_start = fiscal_year.start_date
        
        if period_type == "Month":
            period_num = 1
            while current_start <= fiscal_year.end_date:
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
                
                if current_end >= fiscal_year.end_date: break 
                current_start = current_end + relativedelta(days=1)
                period_num += 1
        
        elif period_type == "Quarter":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                # Calculate end of quarter relative to the fiscal year start, not calendar quarter
                # A simple approach: advance by 3 months, then find end of that month.
                # This might need refinement based on exact quarter definition relative to FY start.
                temp_end = current_start + relativedelta(months=3) - relativedelta(days=1)
                
                # Ensure end of quarter calculation respects fiscal year boundary and doesn't create invalid dates.
                # Example: if FY starts Feb 1, Q1 is Feb,Mar,Apr.
                # Correct logic for arbitrary FY start can be complex. This is a simplified version.
                # For simplicity, just advance 3 months and clamp.
                
                current_end = temp_end
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
        
        # Check if fiscal year is closed
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
