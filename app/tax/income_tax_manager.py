# File: app/tax/income_tax_manager.py
from typing import TYPE_CHECKING 
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.account_service import AccountService # ADDED
    from app.services.fiscal_period_service import FiscalPeriodService # ADDED


class IncomeTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.account_service: "AccountService" = app_core.account_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        self.fiscal_period_service: "FiscalPeriodService" = app_core.fiscal_period_service # type: ignore
        print("IncomeTaxManager initialized (stub).")
    
    async def calculate_provisional_tax(self, fiscal_year_id: int):
        print(f"Calculating provisional tax for fiscal year ID {fiscal_year_id} (stub).")
        return {"provisional_tax_payable": 0.00}

    async def get_form_cs_data(self, fiscal_year_id: int):
        print(f"Fetching data for Form C-S for fiscal year ID {fiscal_year_id} (stub).")
        return {"company_name": "Example Pte Ltd", "revenue": 100000.00, "profit_before_tax": 20000.00}
