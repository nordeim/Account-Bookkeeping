# File: app/business_logic/customer_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.customer import Customer
# REMOVED: from app.services.business_services import CustomerService
# REMOVED: from app.services.account_service import AccountService 
# REMOVED: from app.services.accounting_services import CurrencyService 
from app.utils.result import Result
from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData, CustomerSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.business_services import CustomerService # ADDED
    from app.services.account_service import AccountService # ADDED
    from app.services.accounting_services import CurrencyService # ADDED

class CustomerManager:
    def __init__(self, 
                 customer_service: "CustomerService", 
                 account_service: "AccountService", 
                 currency_service: "CurrencyService", 
                 app_core: "ApplicationCore"):
        self.customer_service = customer_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_customer_for_dialog(self, customer_id: int) -> Optional[Customer]:
        """ Fetches a full customer ORM object for dialog population. """
        try:
            return await self.customer_service.get_by_id(customer_id)
        except Exception as e:
            self.logger.error(f"Error fetching customer ID {customer_id} for dialog: {e}", exc_info=True)
            return None

    async def get_customers_for_listing(self, 
                                       active_only: bool = True,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[CustomerSummaryData]]:
        """ Fetches a list of customer summaries for table display. """
        try:
            summaries: List[CustomerSummaryData] = await self.customer_service.get_all_summary(
                active_only=active_only,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching customer listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve customer list: {str(e)}"])

    async def _validate_customer_data(self, dto: CustomerCreateData | CustomerUpdateData, existing_customer_id: Optional[int] = None) -> List[str]:
        errors: List[str] = []

        if dto.customer_code:
            existing_by_code = await self.customer_service.get_by_code(dto.customer_code)
            if existing_by_code and (existing_customer_id is None or existing_by_code.id != existing_customer_id):
                errors.append(f"Customer code '{dto.customer_code}' already exists.")
        else: 
            errors.append("Customer code is required.") 
            
        if dto.name is None or not dto.name.strip(): 
            errors.append("Customer name is required.")

        if dto.receivables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.receivables_account_id)
            if not acc:
                errors.append(f"Receivables account ID '{dto.receivables_account_id}' not found.")
            elif acc.account_type != 'Asset': 
                errors.append(f"Account '{acc.code} - {acc.name}' is not an Asset account and cannot be used as receivables account.")
            elif not acc.is_active:
                 errors.append(f"Receivables account '{acc.code} - {acc.name}' is not active.")

        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) 
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        else: 
             errors.append("Currency code is required.")
        return errors

    async def create_customer(self, dto: CustomerCreateData) -> Result[Customer]:
        validation_errors = await self._validate_customer_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            customer_orm = Customer(
                customer_code=dto.customer_code, name=dto.name, legal_name=dto.legal_name,
                uen_no=dto.uen_no, gst_registered=dto.gst_registered, gst_no=dto.gst_no,
                contact_person=dto.contact_person, email=str(dto.email) if dto.email else None, phone=dto.phone,
                address_line1=dto.address_line1, address_line2=dto.address_line2,
                postal_code=dto.postal_code, city=dto.city, country=dto.country,
                credit_terms=dto.credit_terms, credit_limit=dto.credit_limit,
                currency_code=dto.currency_code, is_active=dto.is_active,
                customer_since=dto.customer_since, notes=dto.notes,
                receivables_account_id=dto.receivables_account_id,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_customer = await self.customer_service.save(customer_orm)
            return Result.success(saved_customer)
        except Exception as e:
            self.logger.error(f"Error creating customer '{dto.customer_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the customer: {str(e)}"])

    async def update_customer(self, customer_id: int, dto: CustomerUpdateData) -> Result[Customer]:
        existing_customer = await self.customer_service.get_by_id(customer_id)
        if not existing_customer:
            return Result.failure([f"Customer with ID {customer_id} not found."])

        validation_errors = await self._validate_customer_data(dto, existing_customer_id=customer_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_customer, key):
                    if key == 'email' and value is not None: 
                        setattr(existing_customer, key, str(value))
                    else:
                        setattr(existing_customer, key, value)
            
            existing_customer.updated_by_user_id = dto.user_id
            
            updated_customer = await self.customer_service.save(existing_customer)
            return Result.success(updated_customer)
        except Exception as e:
            self.logger.error(f"Error updating customer ID {customer_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the customer: {str(e)}"])

    async def toggle_customer_active_status(self, customer_id: int, user_id: int) -> Result[Customer]:
        customer = await self.customer_service.get_by_id(customer_id)
        if not customer:
            return Result.failure([f"Customer with ID {customer_id} not found."])
        
        customer.is_active = not customer.is_active
        customer.updated_by_user_id = user_id

        try:
            updated_customer = await self.customer_service.save(customer)
            action = "activated" if updated_customer.is_active else "deactivated"
            self.logger.info(f"Customer '{updated_customer.name}' (ID: {customer_id}) {action} by user ID {user_id}.")
            return Result.success(updated_customer)
        except Exception as e:
            self.logger.error(f"Error toggling active status for customer ID {customer_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for customer: {str(e)}"])
