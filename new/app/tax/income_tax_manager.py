# File: app/tax/income_tax_manager.py
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.account_service import AccountService
    from app.services.fiscal_period_service import FiscalPeriodService


class IncomeTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.account_service: "AccountService" = app_core.account_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        self.fiscal_period_service: "FiscalPeriodService" = app_core.fiscal_period_service # type: ignore
        self.logger = app_core.logger
        self.logger.info("IncomeTaxManager initialized.")
    
    async def calculate_provisional_tax(self, fiscal_year_id: int) -> Dict[str, Any]:
        self.logger.info(f"Calculating provisional tax for fiscal year ID {fiscal_year_id} (stub).")
        # In a real implementation, this would fetch the financial data for the ECI period,
        # apply rules (e.g., 75% of taxable income up to a cap is exempt), calculate tax,
        # and determine the provisional tax payable.
        # This would require a call to a report generator like FinancialStatementGenerator.
        return {"provisional_tax_payable": 0.00, "estimated_chargeable_income": 0.00}

    async def get_form_cs_data(self, fiscal_year_id: int) -> Dict[str, Any]:
        self.logger.info(f"Fetching data for Form C-S for fiscal year ID {fiscal_year_id} (stub).")
        # A real implementation would call the FinancialStatementGenerator, get the P&L and BS,
        # and populate a dictionary that maps directly to the fields on Form C-S.
        fy = await self.app_core.fiscal_year_service.get_by_id(fiscal_year_id)
        if not fy:
            return {"error": "Fiscal year not found."}
        
        report = await self.app_core.financial_statement_generator.generate_income_tax_computation(fy)
        
        return {
            "company_name": (await self.app_core.company_settings_service.get_company_settings()).company_name,
            "revenue": report.get('revenue', {}).get('total', 0.00),
            "profit_before_tax": report.get('net_profit_before_tax', 0.00),
            "chargeable_income": report.get('chargeable_income', 0.00)
        }
