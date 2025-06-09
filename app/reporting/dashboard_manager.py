# File: app/reporting/dashboard_manager.py
from typing import Optional, TYPE_CHECKING, List, Dict
from datetime import date
from decimal import Decimal

from app.utils.pydantic_models import DashboardKPIData
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account import Account

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

CURRENT_ASSET_SUBTYPES = ["Cash and Cash Equivalents", "Accounts Receivable", "Inventory", "Prepaid Expenses", "Other Current Assets", "Current Asset"]
CURRENT_LIABILITY_SUBTYPES = ["Accounts Payable", "Accrued Liabilities", "Short-Term Loans", "Current Portion of Long-Term Debt", "GST Payable", "Other Current Liabilities", "Current Liability"]
NON_CURRENT_LIABILITY_SUBTYPES = ["Long-term Liability", "Long-Term Loans"]

class DashboardManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_dashboard_kpis(self, as_of_date: Optional[date] = None) -> Optional[DashboardKPIData]:
        try:
            effective_date = as_of_date if as_of_date is not None else date.today()
            self.logger.info(f"Fetching dashboard KPIs as of {effective_date}...")
            
            company_settings = await self.app_core.company_settings_service.get_company_settings()
            if not company_settings: self.logger.error("Company settings not found."); return None
            base_currency = company_settings.base_currency

            all_fiscal_years_orm: List[FiscalYear] = await self.app_core.fiscal_year_service.get_all()
            current_fy: Optional[FiscalYear] = next((fy for fy in sorted(all_fiscal_years_orm, key=lambda fy: fy.start_date, reverse=True) if fy.start_date <= effective_date <= fy.end_date and not fy.is_closed), None)
            if not current_fy: current_fy = next((fy for fy in sorted(all_fiscal_years_orm, key=lambda fy: fy.start_date, reverse=True) if not fy.is_closed), None)
            if not current_fy and all_fiscal_years_orm: current_fy = max(all_fiscal_years_orm, key=lambda fy: fy.start_date)

            total_revenue_ytd, total_expenses_ytd, net_profit_ytd = Decimal(0), Decimal(0), Decimal(0)
            kpi_period_description = f"As of {effective_date.strftime('%d %b %Y')} (No active FY)"
            if current_fy and effective_date >= current_fy.start_date:
                effective_end_date_for_ytd = min(effective_date, current_fy.end_date)
                kpi_period_description = f"YTD as of {effective_end_date_for_ytd.strftime('%d %b %Y')} (FY: {current_fy.year_name})"
                pl_data = await self.app_core.financial_statement_generator.generate_profit_loss(current_fy.start_date, effective_end_date_for_ytd)
                if pl_data:
                    total_revenue_ytd, total_expenses_ytd, net_profit_ytd = pl_data.get('revenue', {}).get('total', Decimal(0)), pl_data.get('expenses', {}).get('total', Decimal(0)), pl_data.get('net_profit', Decimal(0))
            elif current_fy:
                 kpi_period_description = f"As of {effective_date.strftime('%d %b %Y')} (FY: {current_fy.year_name} not started)"

            current_cash_balance = await self._get_total_cash_balance(base_currency, effective_date)
            total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance(); total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance()
            total_ar_overdue = await self.app_core.customer_service.get_total_overdue_balance(); total_ap_overdue = await self.app_core.vendor_service.get_total_overdue_balance() 
            ar_aging_summary = await self.app_core.customer_service.get_ar_aging_summary(effective_date); ap_aging_summary = await self.app_core.vendor_service.get_ap_aging_summary(effective_date)

            # --- Ratio Calculations ---
            total_current_assets, total_current_liabilities, total_non_current_liabilities, total_inventory, total_equity = (Decimal(0) for _ in range(5))
            all_active_accounts: List[Account] = await self.app_core.account_service.get_all_active()

            for acc in all_active_accounts:
                balance = await self.app_core.journal_service.get_account_balance(acc.id, effective_date)
                if acc.account_type == "Asset":
                    if acc.sub_type in CURRENT_ASSET_SUBTYPES: total_current_assets += balance
                    if acc.sub_type == "Inventory": total_inventory += balance
                elif acc.account_type == "Liability":
                    if acc.sub_type in CURRENT_LIABILITY_SUBTYPES: total_current_liabilities += balance
                    elif acc.sub_type in NON_CURRENT_LIABILITY_SUBTYPES: total_non_current_liabilities += balance
                elif acc.account_type == "Equity": total_equity += balance

            total_liabilities = total_current_liabilities + total_non_current_liabilities
            
            quick_ratio: Optional[Decimal] = None
            if total_current_liabilities > 0: quick_ratio = ((total_current_assets - total_inventory) / total_current_liabilities).quantize(Decimal("0.01"))
            elif (total_current_assets - total_inventory) > 0: quick_ratio = Decimal('Infinity')

            debt_to_equity_ratio: Optional[Decimal] = None
            if total_equity > 0: debt_to_equity_ratio = (total_liabilities / total_equity).quantize(Decimal("0.01"))
            elif total_liabilities > 0: debt_to_equity_ratio = Decimal('Infinity')

            current_ratio: Optional[Decimal] = None
            if total_current_liabilities > 0: current_ratio = (total_current_assets / total_current_liabilities).quantize(Decimal("0.01"))
            elif total_current_assets > 0: current_ratio = Decimal('Infinity')

            return DashboardKPIData(
                kpi_period_description=kpi_period_description, base_currency=base_currency,
                total_revenue_ytd=total_revenue_ytd, total_expenses_ytd=total_expenses_ytd, net_profit_ytd=net_profit_ytd,
                current_cash_balance=current_cash_balance, total_outstanding_ar=total_outstanding_ar, total_outstanding_ap=total_outstanding_ap,
                total_ar_overdue=total_ar_overdue, total_ap_overdue=total_ap_overdue,
                ar_aging_current=ar_aging_summary.get("Current", Decimal(0)), ar_aging_1_30=ar_aging_summary.get("1-30 Days", Decimal(0)),
                ar_aging_31_60=ar_aging_summary.get("31-60 Days", Decimal(0)), ar_aging_61_90=ar_aging_summary.get("61-90 Days", Decimal(0)),
                ar_aging_91_plus=ar_aging_summary.get("91+ Days", Decimal(0)),
                ap_aging_current=ap_aging_summary.get("Current", Decimal(0)), ap_aging_1_30=ap_aging_summary.get("1-30 Days", Decimal(0)),
                ap_aging_31_60=ap_aging_summary.get("31-60 Days", Decimal(0)), ap_aging_61_90=ap_aging_summary.get("61-90 Days", Decimal(0)),
                ap_aging_91_plus=ap_aging_summary.get("91+ Days", Decimal(0)),
                total_current_assets=total_current_assets.quantize(Decimal("0.01")), total_current_liabilities=total_current_liabilities.quantize(Decimal("0.01")),
                total_inventory=total_inventory.quantize(Decimal("0.01")), total_liabilities=total_liabilities.quantize(Decimal("0.01")), total_equity=total_equity.quantize(Decimal("0.01")),
                current_ratio=current_ratio, quick_ratio=quick_ratio, debt_to_equity_ratio=debt_to_equity_ratio
            )
        except Exception as e:
            self.logger.error(f"Error fetching dashboard KPIs: {e}", exc_info=True)
            return None

    async def _get_total_cash_balance(self, base_currency: str, as_of_date: date) -> Decimal:
        active_bank_accounts_summary = await self.app_core.bank_account_service.get_all_summary(active_only=True, currency_code=base_currency, page_size=-1)
        total_cash = sum(ba.current_balance for ba in active_bank_accounts_summary if ba.currency_code == base_currency and ba.current_balance is not None)
        cash_on_hand_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultCash")
        if cash_on_hand_code:
            cash_on_hand_acc = await self.app_core.account_service.get_by_code(cash_on_hand_code)
            if cash_on_hand_acc and cash_on_hand_acc.is_active:
                linked_bank_acc_check = await self.app_core.bank_account_service.get_by_gl_account_id(cash_on_hand_acc.id)
                if not linked_bank_acc_check:
                    total_cash += await self.app_core.journal_service.get_account_balance(cash_on_hand_acc.id, as_of_date)
        return total_cash.quantize(Decimal("0.01"))
