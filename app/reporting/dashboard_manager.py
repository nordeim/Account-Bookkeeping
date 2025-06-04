# File: app/reporting/dashboard_manager.py
from typing import Optional, TYPE_CHECKING, List
from datetime import date
from decimal import Decimal

from app.utils.pydantic_models import DashboardKPIData
from app.models.accounting.fiscal_year import FiscalYear 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class DashboardManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_dashboard_kpis(self) -> Optional[DashboardKPIData]:
        try:
            self.logger.info("Fetching dashboard KPIs...")
            today = date.today()
            
            company_settings = await self.app_core.company_settings_service.get_company_settings()
            if not company_settings:
                self.logger.error("Company settings not found, cannot determine base currency for KPIs.")
                return None
            base_currency = company_settings.base_currency

            all_fiscal_years_orm: List[FiscalYear] = await self.app_core.fiscal_year_service.get_all()
            current_fy: Optional[FiscalYear] = None
            for fy_orm in sorted(all_fiscal_years_orm, key=lambda fy: fy.start_date, reverse=True):
                if fy_orm.start_date <= today <= fy_orm.end_date and not fy_orm.is_closed:
                    current_fy = fy_orm
                    break
            if not current_fy:
                open_fys = [fy_orm for fy_orm in all_fiscal_years_orm if not fy_orm.is_closed]
                if open_fys: current_fy = max(open_fys, key=lambda fy: fy.start_date)
            if not current_fy and all_fiscal_years_orm:
                current_fy = max(all_fiscal_years_orm, key=lambda fy: fy.start_date)

            total_revenue_ytd = Decimal(0)
            total_expenses_ytd = Decimal(0)
            net_profit_ytd = Decimal(0)
            kpi_period_description: str

            if current_fy:
                fy_start_date = current_fy.start_date
                fy_end_date = current_fy.end_date
                effective_end_date_for_ytd = min(today, fy_end_date)
                kpi_period_description = f"YTD as of {effective_end_date_for_ytd.strftime('%d %b %Y')} (FY: {current_fy.year_name})"
                if today >= fy_start_date:
                    pl_data = await self.app_core.financial_statement_generator.generate_profit_loss(
                        start_date=fy_start_date,
                        end_date=effective_end_date_for_ytd
                    )
                    if pl_data:
                        total_revenue_ytd = pl_data.get('revenue', {}).get('total', Decimal(0))
                        total_expenses_ytd = pl_data.get('expenses', {}).get('total', Decimal(0))
                        net_profit_ytd = pl_data.get('net_profit', Decimal(0))
            else:
                self.logger.warning("No fiscal year found. Cannot calculate YTD KPIs.")
                kpi_period_description = f"As of {today.strftime('%d %b %Y')} (No active FY)"

            current_cash_balance = await self._get_total_cash_balance(base_currency)
            total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance()
            total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance()
            total_ar_overdue = await self.app_core.customer_service.get_total_overdue_balance() # New KPI
            total_ap_overdue = await self.app_core.vendor_service.get_total_overdue_balance() # New KPI

            return DashboardKPIData(
                kpi_period_description=kpi_period_description,
                base_currency=base_currency,
                total_revenue_ytd=total_revenue_ytd,
                total_expenses_ytd=total_expenses_ytd,
                net_profit_ytd=net_profit_ytd,
                current_cash_balance=current_cash_balance,
                total_outstanding_ar=total_outstanding_ar,
                total_outstanding_ap=total_outstanding_ap,
                total_ar_overdue=total_ar_overdue, # New field
                total_ap_overdue=total_ap_overdue   # New field
            )
        except Exception as e:
            self.logger.error(f"Error fetching dashboard KPIs: {e}", exc_info=True)
            return None

    async def _get_total_cash_balance(self, base_currency: str) -> Decimal:
        active_bank_accounts = await self.app_core.bank_account_service.get_all_summary(
            active_only=True, 
            currency_code=base_currency,
            page_size=-1 
        )
        total_cash = sum(ba.current_balance for ba in active_bank_accounts if ba.currency_code == base_currency)
        return total_cash if total_cash is not None else Decimal(0)
