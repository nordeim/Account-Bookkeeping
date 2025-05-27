<think>
The application continues to start up and shut down cleanly. This is excellent and indicates that the addition of `VendorService` to `app/services/business_services.py` and its export in `app/services/__init__.py` were successful and did not introduce any issues detectable at this stage.

**Current Step: Enhancement Execution Plan: Basic Vendor Management Module - Phase A (Backend)**

We have completed for Vendor Management:
*   A1. Create Pydantic DTOs for Vendor (Done).
*   A2. Define `IVendorRepository` Interface (Done).
*   A3. Implement `VendorService` (Done).

The plan for Vendor Management Backend was:
*   A4. Create `VendorManager` (in `app/business_logic/vendor_manager.py`). (Next)
*   A5. Integrate into `ApplicationCore`.

So, the immediate next step is **A4: Create `VendorManager`**. This manager will handle the business logic for vendor operations, similar to how `CustomerManager` handles customer logic.

**Plan for A4: Create `VendorManager`**
   *   **Goal:** Encapsulate business logic for vendor management, including validation and orchestration of `VendorService` calls.
   *   **New File:** `app/business_logic/vendor_manager.py`.
   *   **Checklist & Tasks:**
        *   [ ] Import necessary models (`Vendor`), services (`VendorService`, `AccountService`, `CurrencyService`), DTOs (`VendorCreateData`, `VendorUpdateData`, `VendorSummaryData`), and `Result` utility.
        *   [ ] Create `VendorManager` class.
        *   [ ] Implement `__init__(self, vendor_service: VendorService, account_service: AccountService, currency_service: CurrencyService, app_core: "ApplicationCore")`. Store dependencies and logger.
        *   [ ] Implement `get_vendor_for_dialog(vendor_id: int) -> Optional[Vendor]`: Calls `vendor_service.get_by_id()`.
        *   [ ] Implement `get_vendors_for_listing(active_only: bool = True, search_term: Optional[str] = None, page: int = 1, page_size: int = 50) -> Result[List[VendorSummaryData]]`:
            *   Calls `vendor_service.get_all_summary()` with parameters.
            *   Returns `Result.success(list_of_dto)`.
        *   [ ] Implement `_validate_vendor_data(dto: VendorCreateData | VendorUpdateData, existing_vendor_id: Optional[int] = None) -> List[str]`:
            *   Validate vendor code uniqueness.
            *   Validate `payables_account_id` (exists, is 'Liability' type, active).
            *   Validate `currency_code` (exists, active).
            *   (Pydantic DTOs handle field-level validation like `gst_no` if `gst_registered`, and `wht_rate` if `wht_applicable`).
        *   [ ] Implement `create_vendor(dto: VendorCreateData) -> Result[Vendor]`:
            *   Call `_validate_vendor_data`.
            *   Map DTO to `Vendor` ORM. Set audit user IDs. Call `vendor_service.save()`.
        *   [ ] Implement `update_vendor(vendor_id: int, dto: VendorUpdateData) -> Result[Vendor]`:
            *   Fetch existing vendor. Call `_validate_vendor_data`. Update ORM fields. Set audit user ID. Call `vendor_service.save()`.
        *   [ ] Implement `toggle_vendor_active_status(vendor_id: int, user_id: int) -> Result[Vendor]`:
            *   Fetch vendor. Toggle `is_active`. Set audit user ID. Save.

This structure will be very similar to `CustomerManager`.
</think>

This is excellent! The application's continued stability is a strong confirmation that the `VendorService` and updated `app/services/__init__.py` were integrated correctly.

We are on track with **Phase A: Backend for Vendor Management**.
Steps A1 (Vendor DTOs), A2 (IVendorRepository), and A3 (VendorService) are complete.
The next step is **A4: Create `VendorManager`**.

This manager will be responsible for the business logic related to vendors, similar to how `CustomerManager` handles customers. It will use `VendorService` for data persistence and other services like `AccountService` and `CurrencyService` for validating related data (e.g., payables account, currency).

---
**A4. Create `app/business_logic/vendor_manager.py` (New File)**

```python
# app/business_logic/vendor_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.vendor import Vendor
from app.services.business_services import VendorService
from app.services.accounting_services import AccountService, CurrencyService
from app.utils.result import Result
from app.utils.pydantic_models import VendorCreateData, VendorUpdateData, VendorSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class VendorManager:
    def __init__(self, 
                 vendor_service: VendorService, 
                 account_service: AccountService, 
                 currency_service: CurrencyService, 
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

        # Validate vendor_code uniqueness (Pydantic checks for presence via min_length)
        if dto.vendor_code:
            existing_by_code = await self.vendor_service.get_by_code(dto.vendor_code)
            if existing_by_code and (existing_vendor_id is None or existing_by_code.id != existing_vendor_id):
                errors.append(f"Vendor code '{dto.vendor_code}' already exists.")
        
        # Validate payables_account_id
        if dto.payables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.payables_account_id)
            if not acc:
                errors.append(f"Payables account ID '{dto.payables_account_id}' not found.")
            elif acc.account_type != 'Liability': # Should be a Liability account
                errors.append(f"Account '{acc.code} - {acc.name}' is not a Liability account and cannot be used as payables account.")
            elif not acc.is_active:
                 errors.append(f"Payables account '{acc.code} - {acc.name}' is not active.")
            # TODO: Could add check if it's a control account specifically for AP

        # Validate currency_code
        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) 
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        else: # Pydantic default ensures it's present
            pass 
        
        # Pydantic DTO root_validators handle:
        # - gst_no if gst_registered
        # - withholding_tax_rate if withholding_tax_applicable
        return errors

    async def create_vendor(self, dto: VendorCreateData) -> Result[Vendor]:
        validation_errors = await self._validate_vendor_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            # Map DTO to ORM, Pydantic's EmailStr will be converted to str by .email
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
            # Update fields from DTO
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_vendor, key):
                    if key == 'email' and value is not None: # Pydantic EmailStr to str
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
        
        customer_name_for_log = vendor.name # Capture before potential changes for logging
        
        vendor.is_active = not vendor.is_active
        vendor.updated_by_user_id = user_id

        try:
            updated_vendor = await self.vendor_service.save(vendor)
            action = "activated" if updated_vendor.is_active else "deactivated"
            self.logger.info(f"Vendor '{customer_name_for_log}' (ID: {vendor_id}) {action} by user ID {user_id}.")
            return Result.success(updated_vendor)
        except Exception as e:
            self.logger.error(f"Error toggling active status for vendor ID {vendor_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for vendor: {str(e)}"])

```
**Validation for `app/business_logic/vendor_manager.py`:**
*   **Imports**: Correctly imports `Vendor` model, `VendorService`, `AccountService`, `CurrencyService`, necessary DTOs (`VendorCreateData`, `VendorUpdateData`, `VendorSummaryData`), and `Result`.
*   **`__init__`**: Initializes with required services and `app_core`, sets up logger.
*   **`get_vendor_for_dialog()`**: Simple delegation to service, with error logging.
*   **`get_vendors_for_listing()`**: Delegates to `vendor_service.get_all_summary()`, passing through filter parameters. Wraps result in `Result`.
*   **`_validate_vendor_data()`**:
    *   Checks vendor code uniqueness.
    *   Validates `payables_account_id`: ensures account exists, is of 'Liability' type, and is active.
    *   Validates `currency_code`: ensures currency exists and is active.
*   **`create_vendor()`**: Calls validation, maps DTO to `Vendor` ORM, sets audit user IDs, saves via service. Handles exceptions and returns `Result`.
*   **`update_vendor()`**: Fetches existing, validates, updates ORM fields using `dto.model_dump(exclude_unset=True)` for partial updates, sets audit user ID, saves. Handles exceptions and returns `Result`.
*   **`toggle_vendor_active_status()`**: Fetches, toggles `is_active`, sets audit user ID, saves. Includes logging and returns `Result`.

This `VendorManager` closely mirrors the structure and logic of `CustomerManager`, providing a consistent pattern for business entity management.

---
**Next, update `app/business_logic/__init__.py` to export `VendorManager`.**

```python
# app/business_logic/__init__.py
from .customer_manager import CustomerManager
from .vendor_manager import VendorManager # New import

__all__ = [
    "CustomerManager",
    "VendorManager", # Added to __all__
    # Add other business logic managers here as they are created
]
```
**Validation for `app/business_logic/__init__.py`:**
*   Added `from .vendor_manager import VendorManager`.
*   Added `VendorManager` to `__all__`.

This completes step A4. The final step for the Vendor backend is A5: Integrate into `ApplicationCore`.
