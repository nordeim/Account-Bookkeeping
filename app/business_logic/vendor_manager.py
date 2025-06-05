# File: app/business_logic/vendor_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.vendor import Vendor
# REMOVED: from app.services.business_services import VendorService
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.accounting_services import CurrencyService
from app.utils.result import Result
from app.utils.pydantic_models import VendorCreateData, VendorUpdateData, VendorSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.business_services import VendorService # ADDED
    from app.services.account_service import AccountService # ADDED
    from app.services.accounting_services import CurrencyService # ADDED

class VendorManager:
    def __init__(self, 
                 vendor_service: "VendorService", 
                 account_service: "AccountService", 
                 currency_service: "CurrencyService", 
                 app_core: "ApplicationCore"):
        self.vendor_service = vendor_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger 

    async def get_vendor_for_dialog(self, vendor_id: int) -> Optional[Vendor]:
        """ Fetches a full vendor ORM object for dialog population. """
        try:
            return await self.vendor_service.get_by_id(vendor_id)
        except Exception as e:
            self.logger.error(f"Error fetching vendor ID {vendor_id} for dialog: {e}", exc_info=True)
            return None

    async def get_vendors_for_listing(self, 
                                       active_only: bool = True,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[VendorSummaryData]]:
        """ Fetches a list of vendor summaries for table display. """
        try:
            summaries: List[VendorSummaryData] = await self.vendor_service.get_all_summary(
                active_only=active_only,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching vendor listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve vendor list: {str(e)}"])

    async def _validate_vendor_data(self, dto: VendorCreateData | VendorUpdateData, existing_vendor_id: Optional[int] = None) -> List[str]:
        """ Common validation logic for creating and updating vendors. """
        errors: List[str] = []

        if dto.vendor_code:
            existing_by_code = await self.vendor_service.get_by_code(dto.vendor_code)
            if existing_by_code and (existing_vendor_id is None or existing_by_code.id != existing_vendor_id):
                errors.append(f"Vendor code '{dto.vendor_code}' already exists.")
        else: 
            errors.append("Vendor code is required.") 
            
        if dto.name is None or not dto.name.strip(): 
            errors.append("Vendor name is required.")

        if dto.payables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.payables_account_id)
            if not acc:
                errors.append(f"Payables account ID '{dto.payables_account_id}' not found.")
            elif acc.account_type != 'Liability': 
                errors.append(f"Account '{acc.code} - {acc.name}' is not a Liability account and cannot be used as payables account.")
            elif not acc.is_active:
                 errors.append(f"Payables account '{acc.code} - {acc.name}' is not active.")

        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) 
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        else: 
             errors.append("Currency code is required.")
        return errors

    async def create_vendor(self, dto: VendorCreateData) -> Result[Vendor]:
        validation_errors = await self._validate_vendor_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            vendor_orm = Vendor(
                vendor_code=dto.vendor_code, name=dto.name, legal_name=dto.legal_name,
                uen_no=dto.uen_no, gst_registered=dto.gst_registered, gst_no=dto.gst_no,
                withholding_tax_applicable=dto.withholding_tax_applicable,
                withholding_tax_rate=dto.withholding_tax_rate,
                contact_person=dto.contact_person, email=str(dto.email) if dto.email else None, phone=dto.phone,
                address_line1=dto.address_line1, address_line2=dto.address_line2,
                postal_code=dto.postal_code, city=dto.city, country=dto.country,
                payment_terms=dto.payment_terms, currency_code=dto.currency_code, 
                is_active=dto.is_active, vendor_since=dto.vendor_since, notes=dto.notes,
                bank_account_name=dto.bank_account_name, bank_account_number=dto.bank_account_number,
                bank_name=dto.bank_name, bank_branch=dto.bank_branch, bank_swift_code=dto.bank_swift_code,
                payables_account_id=dto.payables_account_id,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_vendor = await self.vendor_service.save(vendor_orm)
            return Result.success(saved_vendor)
        except Exception as e:
            self.logger.error(f"Error creating vendor '{dto.vendor_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the vendor: {str(e)}"])

    async def update_vendor(self, vendor_id: int, dto: VendorUpdateData) -> Result[Vendor]:
        existing_vendor = await self.vendor_service.get_by_id(vendor_id)
        if not existing_vendor:
            return Result.failure([f"Vendor with ID {vendor_id} not found."])

        validation_errors = await self._validate_vendor_data(dto, existing_vendor_id=vendor_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_vendor, key):
                    if key == 'email' and value is not None: 
                        setattr(existing_vendor, key, str(value))
                    else:
                        setattr(existing_vendor, key, value)
            
            existing_vendor.updated_by_user_id = dto.user_id
            
            updated_vendor = await self.vendor_service.save(existing_vendor)
            return Result.success(updated_vendor)
        except Exception as e:
            self.logger.error(f"Error updating vendor ID {vendor_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the vendor: {str(e)}"])

    async def toggle_vendor_active_status(self, vendor_id: int, user_id: int) -> Result[Vendor]:
        vendor = await self.vendor_service.get_by_id(vendor_id)
        if not vendor:
            return Result.failure([f"Vendor with ID {vendor_id} not found."])
        
        vendor_name_for_log = vendor.name 
        
        vendor.is_active = not vendor.is_active
        vendor.updated_by_user_id = user_id

        try:
            updated_vendor = await self.vendor_service.save(vendor)
            action = "activated" if updated_vendor.is_active else "deactivated"
            self.logger.info(f"Vendor '{vendor_name_for_log}' (ID: {vendor_id}) {action} by user ID {user_id}.")
            return Result.success(updated_vendor)
        except Exception as e:
            self.logger.error(f"Error toggling active status for vendor ID {vendor_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for vendor: {str(e)}"])
