# File: app/accounting/currency_manager.py
# (Content as previously generated, verified - needs TYPE_CHECKING for ApplicationCore)
# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.accounting_services import CurrencyService, ExchangeRateService 
from typing import Optional, List, Any, TYPE_CHECKING
from datetime import date
from decimal import Decimal
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class CurrencyManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        # Assuming these service properties exist on app_core and are correctly typed there
        self.currency_service: CurrencyService = app_core.currency_repo_service # type: ignore 
        self.exchange_rate_service: ExchangeRateService = app_core.exchange_rate_service # type: ignore
    
    async def get_active_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all_active()

    async def get_exchange_rate(self, from_currency_code: str, to_currency_code: str, rate_date: date) -> Optional[Decimal]:
        rate_obj = await self.exchange_rate_service.get_rate_for_date(from_currency_code, to_currency_code, rate_date)
        return rate_obj.exchange_rate_value if rate_obj else None

    async def update_exchange_rate(self, from_code:str, to_code:str, r_date:date, rate:Decimal, user_id:int) -> Result[ExchangeRate]:
        existing_rate = await self.exchange_rate_service.get_rate_for_date(from_code, to_code, r_date)
        orm_object: ExchangeRate
        if existing_rate:
            existing_rate.exchange_rate_value = rate
            existing_rate.updated_by_user_id = user_id
            orm_object = existing_rate
        else:
            orm_object = ExchangeRate(
                from_currency_code=from_code, to_currency_code=to_code, rate_date=r_date,
                exchange_rate_value=rate, 
                created_by_user_id=user_id, updated_by_user_id=user_id 
            )
        
        saved_obj = await self.exchange_rate_service.save(orm_object)
        return Result.success(saved_obj)

    async def get_all_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all()

    async def get_currency_by_code(self, code: str) -> Optional[Currency]:
        return await self.currency_service.get_by_id(code)
