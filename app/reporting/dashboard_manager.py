# File: app/reporting/dashboard_manager.py
from typing import Optional, TYPE_CHECKING, List, Dict # Added Dict
from datetime import date
from decimal import Decimal

from app.utils.pydantic_models import DashboardKPIData
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account import Account # For type hinting

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

# Define standard "current" account subtypes. These should ideally match common usage or be configurable.
# These are based on typical Chart of Accounts structures like the general_template.csv.
CURRENT_ASSET_SUBTYPES = [
    "Cash and Cash Equivalents", 
    "Accounts Receivable", 
    "Inventory", 
    "Prepaid Expenses",
    "Other Current Assets", # A generic category
    "Current Asset" # Another generic category often used as a sub_type directly
]
CURRENT_LIABILITY_SUBTYPES = [
    "Accounts Payable", 
    "Accrued Liabilities", 
    "Short-Term Loans", # Assuming "Loans Payable" might be split or if a specific ST Loan subtype exists
    "Current Portion of Long-Term Debt", # If such a subtype exists
    "GST Payable", # Typically current
    "Other Current Liabilities",
    "Current Liability"
]


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
                if today >= fy_start_date: # Ensure we are within or past the start of the current FY
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
            total_ar_overdue = await self.app_core.customer_service.get_total_overdue_balance() 
            total_ap_overdue = await self.app_core.vendor_service.get_total_overdue_balance() 

            # Fetch AR/AP Aging Summaries
            ar_aging_summary = await self.app_core.customer_service.get_ar_aging_summary(as_of_date=today)
            ap_aging_summary = await self.app_core.vendor_service.get_ap_aging_summary(as_of_date=today)

            # Calculate Total Current Assets and Liabilities
            total_current_assets = Decimal(0)
            total_current_liabilities = Decimal(0)
            all_active_accounts: List[Account] = await self.app_core.account_service.get_all_active()

            for acc in all_active_accounts:
                balance = await self.app_core.journal_service.get_account_balance(acc.id, today)
                if acc.account_type == "Asset" and acc.sub_type in CURRENT_ASSET_SUBTYPES:
                    total_current_assets += balance
                elif acc.account_type == "Liability" and acc.sub_type in CURRENT_LIABILITY_SUBTYPES:
                    # JournalService.get_account_balance for liability accounts (credit nature)
                    # returns a positive value if it's a credit balance. Summing these directly is correct.
                    total_current_liabilities += balance 
            
            current_ratio: Optional[Decimal] = None
            if total_current_liabilities > Decimal(0):
                current_ratio = (total_current_assets / total_current_liabilities).quantize(Decimal("0.01"))
            elif total_current_assets > Decimal(0) and total_current_liabilities == Decimal(0):
                current_ratio = Decimal('Infinity') # Represent as None or a very large number for display
                self.logger.warning("Current Liabilities are zero, Current Ratio is effectively infinite.")


            return DashboardKPIData(
                kpi_period_description=kpi_period_description,
                base_currency=base_currency,
                total_revenue_ytd=total_revenue_ytd,
                total_expenses_ytd=total_expenses_ytd,
                net_profit_ytd=net_profit_ytd,
                current_cash_balance=current_cash_balance,
                total_outstanding_ar=total_outstanding_ar,
                total_outstanding_ap=total_outstanding_ap,
                total_ar_overdue=total_ar_overdue, 
                total_ap_overdue=total_ap_overdue,
                ar_aging_current=ar_aging_summary.get("Current", Decimal(0)),
                ar_aging_31_60=ar_aging_summary.get("31-60 Days", Decimal(0)),
                ar_aging_61_90=ar_aging_summary.get("61-90 Days", Decimal(0)),
                ar_aging_91_plus=ar_aging_summary.get("91+ Days", Decimal(0)),
                # Adding 1-30 days for AR (ensure service provides this key or adjust)
                ar_aging_1_30=ar_aging_summary.get("1-30 Days", Decimal(0)),
                ap_aging_current=ap_aging_summary.get("Current", Decimal(0)),
                ap_aging_31_60=ap_aging_summary.get("31-60 Days", Decimal(0)),
                ap_aging_61_90=ap_aging_summary.get("61-90 Days", Decimal(0)),
                ap_aging_91_plus=ap_aging_summary.get("91+ Days", Decimal(0)),
                # Adding 1-30 days for AP
                ap_aging_1_30=ap_aging_summary.get("1-30 Days", Decimal(0)),
                total_current_assets=total_current_assets.quantize(Decimal("0.01")),
                total_current_liabilities=total_current_liabilities.quantize(Decimal("0.01")),
                current_ratio=current_ratio
            )
        except Exception as e:
            self.logger.error(f"Error fetching dashboard KPIs: {e}", exc_info=True)
            return None

    async def _get_total_cash_balance(self, base_currency: str) -> Decimal:
        active_bank_accounts_summary = await self.app_core.bank_account_service.get_all_summary(
            active_only=True, 
            currency_code=base_currency, # Only sum bank accounts in base currency for simplicity
            page_size=-1 
        )
        total_cash = Decimal(0)
        if active_bank_accounts_summary:
            total_cash = sum(ba.current_balance for ba in active_bank_accounts_summary if ba.currency_code == base_currency and ba.current_balance is not None)
        
        # Optionally, add cash on hand GL account balance if distinct from bank GLs
        cash_on_hand_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultCash")
        if cash_on_hand_code:
            cash_on_hand_acc = await self.app_core.account_service.get_by_code(cash_on_hand_code)
            if cash_on_hand_acc and cash_on_hand_acc.is_active:
                 # Check if this GL is NOT already linked to any bank account to avoid double counting
                linked_bank_acc_check = await self.app_core.bank_account_service.get_by_gl_account_id(cash_on_hand_acc.id)
                if not linked_bank_acc_check:
                    cash_on_hand_balance = await self.app_core.journal_service.get_account_balance(cash_on_hand_acc.id, date.today())
                    total_cash += cash_on_hand_balance

        return total_cash.quantize(Decimal("0.01"))
