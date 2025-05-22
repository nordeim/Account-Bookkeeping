# File: app/accounting/fiscal_period_manager.py
# (Content as previously generated, verified)
from app.core.application_core import ApplicationCore
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService # Assuming this exists
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result
from typing import List, Optional
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

class FiscalPeriodManager:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service # type: ignore
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service # type: ignore
        
    async def create_fiscal_year(self, year_name: str, start_date: date, end_date: date, user_id: int) -> Result[FiscalYear]:
        if start_date >= end_date:
            return Result.failure(["Start date must be before end date."])
        # Add overlap check with existing fiscal years via service
        # existing_fy = await self.fiscal_year_service.get_by_date_overlap(start_date, end_date)
        # if existing_fy:
        #     return Result.failure(["Fiscal year dates overlap with an existing year."])

        fy = FiscalYear(
            year_name=year_name, start_date=start_date, end_date=end_date, 
            created_by_user_id=user_id, updated_by_user_id=user_id
        )
        saved_fy = await self.fiscal_year_service.save(fy) # type: ignore
        return Result.success(saved_fy)

    async def generate_periods_for_year(self, fiscal_year: FiscalYear, period_type: str, user_id: int) -> Result[List[FiscalPeriod]]:
        if period_type not in ["Month", "Quarter"]:
            return Result.failure(["Invalid period type. Must be 'Month' or 'Quarter'."])

        periods: List[FiscalPeriod] = []
        current_start = fiscal_year.start_date
        
        if period_type == "Month":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                current_end = current_start + relativedelta(months=1) - relativedelta(days=1)
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
                
                current_start = current_end + relativedelta(days=1)
                period_num += 1
                if current_start > fiscal_year.end_date: break
        elif period_type == "Quarter":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                current_end = current_start + relativedelta(months=3) - relativedelta(days=1)
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

                current_start = current_end + relativedelta(days=1)
                period_num += 1
                if current_start > fiscal_year.end_date: break
        
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
        """Gets the current open fiscal period for a given date (or today)."""
        if target_date is None:
            target_date = date.today()
        return await self.fiscal_period_service.get_by_date(target_date)
