# File: app/reporting/dashboard_manager.py
from typing import Optional, TYPE_CHECKING
from datetime import date
from decimal import Decimal

from app.utils.pydantic_models import DashboardKPIData
from app.models.accounting.fiscal_year import FiscalYear # For type hint

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
            
            # 1. Get Base Currency
            company_settings = await self.app_core.company_settings_service.get_company_settings()
            if not company_settings:
                self.logger.error("Company settings not found, cannot determine base currency for KPIs.")
                return None
            base_currency = company_settings.base_currency

            # 2. Determine Current Fiscal Year Start Date
            # Attempt to find a fiscal year that contains today's date and is not closed.
            # If multiple, pick the one that started most recently.
            # If none, try the most recent closed one.
            all_fiscal_years_orm: List[FiscalYear] = await self.app_core.fiscal_year_service.get_all()
            
            current_fy: Optional[FiscalYear] = None
            # Prefer open fiscal year containing today
            for fy_orm in sorted(all_fiscal_years_orm, key=lambda fy: fy.start_date, reverse=True):
                if fy_orm.start_date <= today <= fy_orm.end_date and not fy_orm.is_closed:
                    current_fy = fy_orm
                    break
            
            # Fallback: most recent open fiscal year if today is outside any open FY
            if not current_fy:
                open_fys = [fy_orm for fy_orm in all_fiscal_years_orm if not fy_orm.is_closed]
                if open_fys:
                    current_fy = max(open_fys, key=lambda fy: fy.start_date)
            
            # Fallback: most recent fiscal year overall if no open ones
            if not current_fy and all_fiscal_years_orm:
                current_fy = max(all_fiscal_years_orm, key=lambda fy: fy.start_date)

            if not current_fy:
                self.logger.warning("No fiscal year found. Cannot calculate YTD KPIs.")
                # Return with available non-YTD data if possible, or all zeros/None
                kpi_period_description = f"As of {today.strftime('%d %b %Y')} (No active FY)"
                # Fallback logic for cash, AR, AP if FY independent
                current_cash_balance = await self._get_total_cash_balance(base_currency)
                total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance()
                total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance()
                return DashboardKPIData(
                    kpi_period_description=kpi_period_description,
                    base_currency=base_currency,
                    total_revenue_ytd=Decimal(0), total_expenses_ytd=Decimal(0), net_profit_ytd=Decimal(0),
                    current_cash_balance=current_cash_balance,
                    total_outstanding_ar=total_outstanding_ar,
                    total_outstanding_ap=total_outstanding_ap
                )

            fy_start_date = current_fy.start_date
            fy_end_date = current_fy.end_date # Not strictly 'today' if FY is historical
            effective_end_date_for_ytd = min(today, fy_end_date) # YTD is up to today or FY end, whichever is earlier

            kpi_period_description = f"YTD as of {effective_end_date_for_ytd.strftime('%d %b %Y')} (FY: {current_fy.year_name})"
            
            # 3. P&L KPIs (Revenue, Expense, Net Profit YTD)
            # Assuming generate_profit_loss calculates based on specified period.
            # If today is before fy_start_date, P&L figures should be 0.
            total_revenue_ytd = Decimal(0)
            total_expenses_ytd = Decimal(0)
            net_profit_ytd = Decimal(0)

            if today >= fy_start_date:
                pl_data = await self.app_core.financial_statement_generator.generate_profit_loss(
                    start_date=fy_start_date,
                    end_date=effective_end_date_for_ytd
                )
                if pl_data:
                    total_revenue_ytd = pl_data.get('revenue', {}).get('total', Decimal(0))
                    total_expenses_ytd = pl_data.get('expenses', {}).get('total', Decimal(0))
                    net_profit_ytd = pl_data.get('net_profit', Decimal(0))
            
            # 4. Current Cash Balance
            # Simpler: Sum current_balance from BankAccount where currency is base_currency
            current_cash_balance = await self._get_total_cash_balance(base_currency)

            # 5. Total Outstanding AR
            # Assumption: get_total_outstanding_balance returns sum in base currency or effectively so.
            total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance()

            # 6. Total Outstanding AP
            total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance()

            return DashboardKPIData(
                kpi_period_description=kpi_period_description,
                base_currency=base_currency,
                total_revenue_ytd=total_revenue_ytd,
                total_expenses_ytd=total_expenses_ytd,
                net_profit_ytd=net_profit_ytd,
                current_cash_balance=current_cash_balance,
                total_outstanding_ar=total_outstanding_ar,
                total_outstanding_ap=total_outstanding_ap
            )

        except Exception as e:
            self.logger.error(f"Error fetching dashboard KPIs: {e}", exc_info=True)
            return None

    async def _get_total_cash_balance(self, base_currency: str) -> Decimal:
        """
        Calculates total cash balance from active bank accounts in the specified base currency.
        Multi-currency bank accounts not in base currency are currently ignored for this KPI.
        """
        active_bank_accounts = await self.app_core.bank_account_service.get_all_summary(
            active_only=True, 
            currency_code=base_currency, # Filter by base currency
            page_size=-1 # Get all
        )
        total_cash = sum(ba.current_balance for ba in active_bank_accounts if ba.currency_code == base_currency)
        
        # Additionally, consider cash on hand from CoA if such accounts exist and are tracked separately
        # For now, relying on BankAccount balances.
        
        return total_cash if total_cash is not None else Decimal(0)
