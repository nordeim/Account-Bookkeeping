<think>
The application continues to launch and shut down cleanly. This indicates that adding the `ICustomerRepository` interface to `app/services/__init__.py` and creating the `app/services/business_services.py` file with `CustomerService` did not introduce any startup/shutdown issues or import errors visible at this stage.

**Current Step: Enhancement Execution Plan: Basic Customer Management Module - Phase A (Backend)**

We have completed:
*   A1. Create Pydantic DTOs for Customer (Done)
*   A2. Define `ICustomerRepository` Interface (Done)
*   A3. Implement `CustomerService` (Done)

The next logical step is **A4: Create `CustomerManager`**.

**Plan for A4: Create `CustomerManager`**
   *   **Goal:** Encapsulate business logic for customer management, validation, and interaction with `CustomerService`.
   *   **New File:** `app/business_logic/customer_manager.py`.
   *   **Checklist & Tasks:**
        *   Create `CustomerManager(__init__(self, customer_service: CustomerService, account_service: AccountService, currency_service: CurrencyService, app_core: "ApplicationCore"))`.
            *   It will need `AccountService` to validate `receivables_account_id` and `CurrencyService` to validate `currency_code`.
        *   Implement `get_customer_for_dialog(customer_id: int) -> Optional[Customer]`: Calls `customer_service.get_by_id()`.
        *   Implement `get_customers_for_listing(filters: Optional[Dict[str, Any]] = None) -> Result[List[CustomerSummaryData]]`:
            *   Extract `search_term`, `active_only`, `page`, `page_size` from filters.
            *   Calls `customer_service.get_all_summary()` with these parameters.
            *   Returns `Result.success(list_of_dto)`.
        *   Implement `create_customer(dto: CustomerCreateData) -> Result[Customer]`:
            *   Perform validations:
                *   Customer code uniqueness using `customer_service.get_by_code()`.
                *   If `dto.receivables_account_id` is provided, validate it exists using `account_service.get_by_id()` and is an 'Asset' type account (or more specifically, an AR control account if sub-types are used).
                *   If `dto.currency_code` is provided, validate it exists using `currency_service.get_by_id()`.
            *   Map `CustomerCreateData` to `Customer` ORM model.
            *   Set `created_by_user_id = dto.user_id`, `updated_by_user_id = dto.user_id`.
            *   Call `customer_service.save()`.
            *   Return `Result.success(customer)` or `Result.failure(errors)`.
        *   Implement `update_customer(customer_id: int, dto: CustomerUpdateData) -> Result[Customer]`:
            *   Fetch existing `Customer` using `customer_service.get_by_id()`.
            *   If code is changed, validate new code uniqueness.
            *   Validate `receivables_account_id` and `currency_code` if changed.
            *   Update ORM fields from DTO.
            *   Set `updated_by_user_id = dto.user_id`.
            *   Call `customer_service.save()`.
            *   Return `Result`.
        *   Implement `toggle_customer_active_status(customer_id: int, user_id: int) -> Result[Customer]`:
            *   Fetch customer.
            *   (Future check: Prevent deactivation if outstanding invoices/balance).
            *   Toggle `is_active` flag.
            *   Set `updated_by_user_id`.
            *   Call `customer_service.save()`.
            *   Return `Result`.

I will need to create the directory `app/business_logic/` and an `__init__.py` file within it if they don't exist, then create `customer_manager.py`.
For the `__init__` method of `CustomerManager`, it will need `AccountService` and `CurrencyService` in addition to `CustomerService` and `app_core`. These will be injected by `ApplicationCore`.
</think>

Excellent! The application remains stable after the previous backend additions for the Customer module.

We'll now proceed with **Step A4: Create `CustomerManager`** from the "Enhancement Execution Plan: Basic Customer Management Module - Phase A (Backend)".

This manager will encapsulate the business logic for customer operations, including validations and orchestrating calls to the `CustomerService` and other relevant services (like `AccountService` for validating receivables accounts and `CurrencyService` for currency codes).

---
**1. Create `app/business_logic/__init__.py` (New File, if directory doesn't exist)**

This file simply makes the `business_logic` directory a Python package and can be used to export its contents.

```python
# app/business_logic/__init__.py
from .customer_manager import CustomerManager

__all__ = [
    "CustomerManager",
    # Add other business logic managers here as they are created (e.g., VendorManager, ProductManager)
]
```

---
**2. Create `app/business_logic/customer_manager.py` (New File)**

```python
# app/business_logic/customer_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.customer import Customer
from app.services.business_services import CustomerService # Assuming CustomerService is in business_services
from app.services.accounting_services import AccountService, CurrencyService # For validation
from app.utils.result import Result
from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData, CustomerSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerManager:
    def __init__(self, 
                 customer_service: CustomerService, 
                 account_service: AccountService, # For validating receivables_account_id
                 currency_service: CurrencyService, # For validating currency_code
                 app_core: "ApplicationCore"):
        self.customer_service = customer_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger # Use logger from app_core

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
            summaries = await self.customer_service.get_all_summary(
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
        """ Common validation logic for create and update. """
        errors: List[str] = []

        # Validate customer_code uniqueness
        if dto.customer_code:
            existing_by_code = await self.customer_service.get_by_code(dto.customer_code)
            if existing_by_code and (existing_customer_id is None or existing_by_code.id != existing_customer_id):
                errors.append(f"Customer code '{dto.customer_code}' already exists.")
        
        # Validate receivables_account_id
        if dto.receivables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.receivables_account_id)
            if not acc:
                errors.append(f"Receivables account ID '{dto.receivables_account_id}' not found.")
            elif acc.account_type != 'Asset': # Could be more specific, e.g. sub_type 'Accounts Receivable'
                errors.append(f"Account '{acc.code} - {acc.name}' is not an Asset account and cannot be used as receivables account.")
            elif not acc.is_active:
                 errors.append(f"Receivables account '{acc.code} - {acc.name}' is not active.")
            # TODO: Could add check if it's a control account specifically for AR

        # Validate currency_code
        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) # get_by_id uses code for Currency
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found or is not active.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        
        # Pydantic DTO itself handles many field-level validations (e.g., email format, lengths)
        # Add any other cross-field or business rule validations here.

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
            existing_customer.customer_code = dto.customer_code
            existing_customer.name = dto.name
            existing_customer.legal_name = dto.legal_name
            existing_customer.uen_no = dto.uen_no
            existing_customer.gst_registered = dto.gst_registered
            existing_customer.gst_no = dto.gst_no
            existing_customer.contact_person = dto.contact_person
            existing_customer.email = str(dto.email) if dto.email else None
            existing_customer.phone = dto.phone
            existing_customer.address_line1 = dto.address_line1
            existing_customer.address_line2 = dto.address_line2
            existing_customer.postal_code = dto.postal_code
            existing_customer.city = dto.city
            existing_customer.country = dto.country
            existing_customer.credit_terms = dto.credit_terms
            existing_customer.credit_limit = dto.credit_limit
            existing_customer.currency_code = dto.currency_code
            existing_customer.is_active = dto.is_active
            existing_customer.customer_since = dto.customer_since
            existing_customer.notes = dto.notes
            existing_customer.receivables_account_id = dto.receivables_account_id
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

        # Future validation: Check for outstanding invoices or balances before deactivating.
        # For now, simple toggle.
        # if customer.is_active:
        #     outstanding_balance = # ... call a method to get balance ...
        #     if outstanding_balance != Decimal(0):
        #         return Result.failure([f"Cannot deactivate customer '{customer.name}'. Outstanding balance exists."])
        
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

```
**Validation for `app/business_logic/customer_manager.py`:**
*   Created new directory `app/business_logic` and new file `customer_manager.py`.
*   `__init__`: Takes `CustomerService`, `AccountService`, `CurrencyService`, and `app_core`. Initializes `self.logger`.
*   `get_customer_for_dialog()`: Calls service method, includes basic error logging.
*   `get_customers_for_listing()`: Calls `customer_service.get_all_summary()` passing through filter parameters. Returns `Result` with `List[CustomerSummaryData]`.
*   `_validate_customer_data()`: Private helper for common validations (code uniqueness, receivables account existence/type/activity, currency existence/activity).
*   `create_customer()`: Calls `_validate_customer_data`, maps DTO to ORM, sets audit user IDs, saves via service. Returns `Result`.
*   `update_customer()`: Fetches existing, calls `_validate_customer_data`, updates ORM fields, sets audit user ID, saves via service. Returns `Result`.
*   `toggle_customer_active_status()`: Fetches, toggles `is_active`, sets audit user ID, saves. Returns `Result`. Includes basic logging.

---
**Next, I will update `app/core/application_core.py` to integrate these new components.**
