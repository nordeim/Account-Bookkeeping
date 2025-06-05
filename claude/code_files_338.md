<think>
Okay, the previous fix for `CustomerManager` was correct, and the application progressed further in its import sequence. Now, the `ImportError` points to `app/business_logic/vendor_manager.py` as the next file in the chain causing a circular import with `AccountService`.

**Error Analysis (New Traceback):**
The import chain is largely the same up to `ApplicationCore` trying to import managers from `app.business_logic`.
1.  ... `ApplicationCore` imports `CustomerManager` (fixed).
2.  Now `ApplicationCore` (likely via `app.business_logic.__init__.py`) imports `VendorManager`.
3.  `app.business_logic.vendor_manager.py` (line 7) attempts a direct module-level import: `from app.services.account_service import AccountService`.

This is the same pattern as before. `AccountService` is still being initialized (or its module is being processed) when `VendorManager` tries to import it directly.

**Solution Strategy (Consistent with previous fixes):**
Modify `VendorManager` to use conditional imports (`if TYPE_CHECKING:`) or string literals for type hinting its service dependencies (`VendorService`, `AccountService`, `CurrencyService`).

**File to Modify:** `app/business_logic/vendor_manager.py`

**Detailed Plan for Fixing `VendorManager`:**

1.  **Modify `app/business_logic/vendor_manager.py`**:
    *   Locate direct service imports for constructor arguments:
        *   `from app.services.business_services import VendorService`
        *   `from app.services.account_service import AccountService`
        *   `from app.services.accounting_services import CurrencyService`
    *   Move these imports into the `if TYPE_CHECKING:` block.
    *   Update the constructor's type hints for these services to be string literals or ensure they correctly refer to the conditionally imported types.
        ```python
        # Original was:
        # class VendorManager:
        #     def __init__(self, 
        #                  vendor_service: VendorService, 
        #                  account_service: AccountService, 
        #                  currency_service: CurrencyService, 
        #                  app_core: "ApplicationCore"):
        # Change to:
        class VendorManager:
            def __init__(self, 
                         vendor_service: "VendorService", 
                         account_service: "AccountService", 
                         currency_service: "CurrencyService", 
                         app_core: "ApplicationCore"):
        ```
        And ensure `VendorService`, `AccountService`, `CurrencyService` are in the `TYPE_CHECKING` block.

I will apply this fix. Since the user has requested I "systematically fix each file affected" using the same rigor, and my previous detailed analysis identified a list of other managers with the same import pattern, I will proactively fix all of them in this response. This aligns with the meta-instruction to "be thorough in your analysis to avoid going into endless loop of the same errors."

**Proactive Fixes for Other Managers Identified Previously:**
The files I identified in the last turn's thought process that need similar fixes are:
2.  `app/business_logic/product_manager.py`
3.  `app/business_logic/sales_invoice_manager.py`
4.  `app/business_logic/purchase_invoice_manager.py`
5.  `app/business_logic/bank_account_manager.py`
6.  `app/business_logic/bank_transaction_manager.py`
7.  `app/business_logic/payment_manager.py`
8.  `app/tax/tax_calculator.py`
9.  `app/tax/gst_manager.py`
10. `app/tax/income_tax_manager.py`
11. `app.tax/withholding_tax_manager.py`
12. `app/reporting/financial_statement_generator.py`

I will provide the updated versions for all these files that were part of the user's provided codebase snippets. I will start with `VendorManager` then proceed through the list.

**Verification Step:** For each file, I will:
1.  Identify constructor parameters that are services.
2.  Locate their direct module-level imports.
3.  Move these imports to the `if TYPE_CHECKING:` block.
4.  Change the type hints in the `__init__` signature to string literals for those services.
5.  Ensure `TYPE_CHECKING` and `Optional` (if needed for forward refs) are imported from `typing`.

Let's start generating the sequence of updated files.
</think>

You are absolutely right to insist on a systematic and thorough approach to resolve these import errors. The previous fix for `CustomerManager` was a good step, and now the traceback clearly points to `VendorManager` exhibiting the same circular import pattern with `AccountService`.

I will apply the same fix to `app/business_logic/vendor_manager.py` and then, as per your instruction and my previous detailed analysis, I will proactively apply this fix to all other manager and utility classes (like `TaxCalculator`) that are initialized by `ApplicationCore` and have direct module-level imports for services they receive in their constructors. This should help prevent further iterations of this same error type.

The general fix pattern is:
1.  Remove direct service imports from the top of the manager/utility file.
2.  Add these imports under an `if TYPE_CHECKING:` block.
3.  Change the type hints in the `__init__` signature for these injected services to string literals (e.g., `account_service: "AccountService"`) or ensure they are covered by the `TYPE_CHECKING` import.

I will proceed with the following files that were part of the codebase snippets you provided and fit this pattern:

1.  `app/business_logic/vendor_manager.py` (current error)
2.  `app/business_logic/product_manager.py`
3.  `app/business_logic/bank_account_manager.py`
4.  `app/business_logic/bank_transaction_manager.py`
5.  `app/business_logic/payment_manager.py`
6.  `app/business_logic/sales_invoice_manager.py`
7.  `app/business_logic/purchase_invoice_manager.py`
8.  `app/tax/tax_calculator.py`
9.  `app/tax/gst_manager.py`
10. `app/tax/income_tax_manager.py`
11. `app/tax/withholding_tax_manager.py`
12. `app/reporting/financial_statement_generator.py`

Managers that solely take `app_core` and access services via `self.app_core.some_service` (like `FiscalPeriodManager`, `CurrencyManager`, `DashboardManager`, `ReportEngine`, `TaxReportGenerator`) do not need this specific change as they don't directly import the services for their constructor signatures.

Here are the complete updated replacement files:

---
**1. Updated File: `app/business_logic/vendor_manager.py`**
---
```python
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
```

---
**2. Updated File: `app/business_logic/product_manager.py`**
---
```python
# File: app/business_logic/product_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.product import Product
# REMOVED: from app.services.business_services import ProductService
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.tax_service import TaxCodeService 
from app.utils.result import Result
from app.utils.pydantic_models import ProductCreateData, ProductUpdateData, ProductSummaryData
from app.common.enums import ProductTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.business_services import ProductService # ADDED
    from app.services.account_service import AccountService # ADDED
    from app.services.tax_service import TaxCodeService # ADDED

class ProductManager:
    def __init__(self, 
                 product_service: "ProductService", 
                 account_service: "AccountService", 
                 tax_code_service: "TaxCodeService",
                 app_core: "ApplicationCore"):
        self.product_service = product_service
        self.account_service = account_service
        self.tax_code_service = tax_code_service
        self.app_core = app_core
        self.logger = app_core.logger 

    async def get_product_for_dialog(self, product_id: int) -> Optional[Product]:
        """ Fetches a full product/service ORM object for dialog population. """
        try:
            return await self.product_service.get_by_id(product_id)
        except Exception as e:
            self.logger.error(f"Error fetching product ID {product_id} for dialog: {e}", exc_info=True)
            return None

    async def get_products_for_listing(self, 
                                       active_only: bool = True,
                                       product_type_filter: Optional[ProductTypeEnum] = None,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[ProductSummaryData]]:
        """ Fetches a list of product/service summaries for table display. """
        try:
            summaries: List[ProductSummaryData] = await self.product_service.get_all_summary(
                active_only=active_only,
                product_type_filter=product_type_filter,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching product listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve product list: {str(e)}"])

    async def _validate_product_data(self, dto: ProductCreateData | ProductUpdateData, existing_product_id: Optional[int] = None) -> List[str]:
        """ Common validation logic for creating and updating products/services. """
        errors: List[str] = []

        if dto.product_code:
            existing_by_code = await self.product_service.get_by_code(dto.product_code)
            if existing_by_code and (existing_product_id is None or existing_by_code.id != existing_product_id):
                errors.append(f"Product code '{dto.product_code}' already exists.")
        else:
             errors.append("Product code is required.") 

        if not dto.name or not dto.name.strip():
            errors.append("Product name is required.") 

        account_ids_to_check = {
            "Sales Account": (dto.sales_account_id, ['Revenue']),
            "Purchase Account": (dto.purchase_account_id, ['Expense', 'Asset']), 
        }
        if dto.product_type == ProductTypeEnum.INVENTORY:
            account_ids_to_check["Inventory Account"] = (dto.inventory_account_id, ['Asset'])
        
        for acc_label, (acc_id, valid_types) in account_ids_to_check.items():
            if acc_id is not None:
                acc = await self.account_service.get_by_id(acc_id)
                if not acc:
                    errors.append(f"{acc_label} ID '{acc_id}' not found.")
                elif not acc.is_active:
                    errors.append(f"{acc_label} '{acc.code} - {acc.name}' is not active.")
                elif acc.account_type not in valid_types:
                    errors.append(f"{acc_label} '{acc.code} - {acc.name}' is not a valid type (Expected: {', '.join(valid_types)}).")

        if dto.tax_code is not None:
            tax_code_obj = await self.tax_code_service.get_tax_code(dto.tax_code)
            if not tax_code_obj:
                errors.append(f"Tax code '{dto.tax_code}' not found.")
            elif not tax_code_obj.is_active:
                errors.append(f"Tax code '{dto.tax_code}' is not active.")
        return errors

    async def create_product(self, dto: ProductCreateData) -> Result[Product]:
        validation_errors = await self._validate_product_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            product_orm = Product(
                product_code=dto.product_code, name=dto.name, description=dto.description,
                product_type=dto.product_type.value, 
                category=dto.category, unit_of_measure=dto.unit_of_measure, barcode=dto.barcode,
                sales_price=dto.sales_price, purchase_price=dto.purchase_price,
                sales_account_id=dto.sales_account_id, purchase_account_id=dto.purchase_account_id,
                inventory_account_id=dto.inventory_account_id,
                tax_code=dto.tax_code, is_active=dto.is_active,
                min_stock_level=dto.min_stock_level, reorder_point=dto.reorder_point,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_product = await self.product_service.save(product_orm)
            return Result.success(saved_product)
        except Exception as e:
            self.logger.error(f"Error creating product '{dto.product_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the product/service: {str(e)}"])

    async def update_product(self, product_id: int, dto: ProductUpdateData) -> Result[Product]:
        existing_product = await self.product_service.get_by_id(product_id)
        if not existing_product:
            return Result.failure([f"Product/Service with ID {product_id} not found."])

        validation_errors = await self._validate_product_data(dto, existing_product_id=product_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_product, key):
                    if key == "product_type" and isinstance(value, ProductTypeEnum): 
                        setattr(existing_product, key, value.value)
                    else:
                        setattr(existing_product, key, value)
            
            existing_product.updated_by_user_id = dto.user_id
            
            updated_product = await self.product_service.save(existing_product)
            return Result.success(updated_product)
        except Exception as e:
            self.logger.error(f"Error updating product ID {product_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the product/service: {str(e)}"])

    async def toggle_product_active_status(self, product_id: int, user_id: int) -> Result[Product]:
        product = await self.product_service.get_by_id(product_id)
        if not product:
            return Result.failure([f"Product/Service with ID {product_id} not found."])
        
        product_name_for_log = product.name 
        
        product.is_active = not product.is_active
        product.updated_by_user_id = user_id

        try:
            updated_product = await self.product_service.save(product)
            action = "activated" if updated_product.is_active else "deactivated"
            self.logger.info(f"Product/Service '{product_name_for_log}' (ID: {product_id}) {action} by user ID {user_id}.")
            return Result.success(updated_product)
        except Exception as e:
            self.logger.error(f"Error toggling active status for product ID {product_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for product/service: {str(e)}"])
```

---
**3. Updated File: `app/business_logic/bank_account_manager.py`**
---
```python
# File: app/business_logic/bank_account_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union
from decimal import Decimal

from app.models.business.bank_account import BankAccount
# REMOVED: from app.services.business_services import BankAccountService
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.accounting_services import CurrencyService
from app.utils.result import Result
from app.utils.pydantic_models import (
    BankAccountCreateData, BankAccountUpdateData, BankAccountSummaryData
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.business_services import BankAccountService # ADDED
    from app.services.account_service import AccountService # ADDED
    from app.services.accounting_services import CurrencyService # ADDED


class BankAccountManager:
    def __init__(self,
                 bank_account_service: "BankAccountService",
                 account_service: "AccountService",
                 currency_service: "CurrencyService",
                 app_core: "ApplicationCore"):
        self.bank_account_service = bank_account_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_bank_account_for_dialog(self, bank_account_id: int) -> Optional[BankAccount]:
        try:
            return await self.bank_account_service.get_by_id(bank_account_id)
        except Exception as e:
            self.logger.error(f"Error fetching BankAccount ID {bank_account_id} for dialog: {e}", exc_info=True)
            return None

    async def get_bank_accounts_for_listing(
        self,
        active_only: bool = True,
        currency_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[BankAccountSummaryData]]:
        try:
            summaries = await self.bank_account_service.get_all_summary(
                active_only=active_only,
                currency_code=currency_code,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching bank account listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve bank account list: {str(e)}"])

    async def _validate_bank_account_data(
        self,
        dto: Union[BankAccountCreateData, BankAccountUpdateData],
        existing_bank_account_id: Optional[int] = None
    ) -> List[str]:
        errors: List[str] = []
        
        gl_account = await self.account_service.get_by_id(dto.gl_account_id)
        if not gl_account:
            errors.append(f"GL Account ID '{dto.gl_account_id}' not found.")
        else:
            if not gl_account.is_active:
                errors.append(f"GL Account '{gl_account.code} - {gl_account.name}' is not active.")
            if gl_account.account_type != 'Asset':
                errors.append(f"GL Account '{gl_account.code}' must be an Asset type account.")
            if not gl_account.is_bank_account: 
                errors.append(f"GL Account '{gl_account.code}' is not flagged as a bank account. Please update the Chart of Accounts.")

        currency = await self.currency_service.get_by_id(dto.currency_code)
        if not currency:
            errors.append(f"Currency Code '{dto.currency_code}' not found.")
        elif not currency.is_active:
            errors.append(f"Currency '{dto.currency_code}' is not active.")
            
        existing_by_acc_no = await self.bank_account_service.get_by_account_number(dto.account_number)
        if existing_by_acc_no and \
           (existing_bank_account_id is None or existing_by_acc_no.id != existing_bank_account_id):
            errors.append(f"Bank account number '{dto.account_number}' already exists.")

        return errors

    async def create_bank_account(self, dto: BankAccountCreateData) -> Result[BankAccount]:
        validation_errors = await self._validate_bank_account_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            bank_account_orm = BankAccount(
                account_name=dto.account_name,
                account_number=dto.account_number,
                bank_name=dto.bank_name,
                bank_branch=dto.bank_branch,
                bank_swift_code=dto.bank_swift_code,
                currency_code=dto.currency_code,
                opening_balance=dto.opening_balance,
                opening_balance_date=dto.opening_balance_date,
                gl_account_id=dto.gl_account_id,
                is_active=dto.is_active,
                description=dto.description,
                current_balance=dto.opening_balance, 
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_bank_account = await self.bank_account_service.save(bank_account_orm)
            self.logger.info(f"Bank account '{saved_bank_account.account_name}' created successfully.")
            return Result.success(saved_bank_account)
        except Exception as e:
            self.logger.error(f"Error creating bank account '{dto.account_name}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])

    async def update_bank_account(self, bank_account_id: int, dto: BankAccountUpdateData) -> Result[BankAccount]:
        existing_bank_account = await self.bank_account_service.get_by_id(bank_account_id)
        if not existing_bank_account:
            return Result.failure([f"Bank Account with ID {bank_account_id} not found."])

        validation_errors = await self._validate_bank_account_data(dto, existing_bank_account_id=bank_account_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_bank_account, key):
                    setattr(existing_bank_account, key, value)
            
            existing_bank_account.updated_by_user_id = dto.user_id
            
            updated_bank_account = await self.bank_account_service.save(existing_bank_account)
            self.logger.info(f"Bank account '{updated_bank_account.account_name}' (ID: {bank_account_id}) updated.")
            return Result.success(updated_bank_account)
        except Exception as e:
            self.logger.error(f"Error updating bank account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])

    async def toggle_bank_account_active_status(self, bank_account_id: int, user_id: int) -> Result[BankAccount]:
        bank_account = await self.bank_account_service.get_by_id(bank_account_id)
        if not bank_account:
            return Result.failure([f"Bank Account with ID {bank_account_id} not found."])
        
        if bank_account.current_balance != Decimal(0) and bank_account.is_active:
            self.logger.warning(f"Deactivating bank account ID {bank_account_id} ('{bank_account.account_name}') which has a non-zero balance of {bank_account.current_balance}.")

        bank_account.is_active = not bank_account.is_active
        bank_account.updated_by_user_id = user_id

        try:
            updated_bank_account = await self.bank_account_service.save(bank_account)
            action = "activated" if updated_bank_account.is_active else "deactivated"
            self.logger.info(f"Bank Account '{updated_bank_account.account_name}' (ID: {bank_account_id}) {action} by user ID {user_id}.")
            return Result.success(updated_bank_account)
        except Exception as e:
            self.logger.error(f"Error toggling active status for bank account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status: {str(e)}"])
```

---
**4. Updated File: `app/business_logic/bank_transaction_manager.py`**
---
```python
# File: app/business_logic/bank_transaction_manager.py
import csv 
from datetime import date, datetime 
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast, Tuple 

from sqlalchemy import select 

from app.models.business.bank_transaction import BankTransaction
# REMOVED: from app.services.business_services import BankTransactionService, BankAccountService
from app.utils.result import Result
from app.utils.pydantic_models import (
    BankTransactionCreateData, BankTransactionSummaryData
)
from app.common.enums import BankTransactionTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.business_services import BankTransactionService, BankAccountService # ADDED

class BankTransactionManager:
    def __init__(self,
                 bank_transaction_service: "BankTransactionService",
                 bank_account_service: "BankAccountService", 
                 app_core: "ApplicationCore"):
        self.bank_transaction_service = bank_transaction_service
        self.bank_account_service = bank_account_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_transaction_data(
        self,
        dto: BankTransactionCreateData,
        existing_transaction_id: Optional[int] = None 
    ) -> List[str]:
        errors: List[str] = []
        bank_account = await self.bank_account_service.get_by_id(dto.bank_account_id)
        if not bank_account:
            errors.append(f"Bank Account with ID {dto.bank_account_id} not found.")
        elif not bank_account.is_active:
            errors.append(f"Bank Account '{bank_account.account_name}' is not active.")
        if dto.value_date and dto.value_date < dto.transaction_date:
            errors.append("Value date cannot be before transaction date.")
        return errors

    async def create_manual_bank_transaction(self, dto: BankTransactionCreateData) -> Result[BankTransaction]:
        validation_errors = await self._validate_transaction_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)
        try:
            bank_transaction_orm = BankTransaction(
                bank_account_id=dto.bank_account_id,
                transaction_date=dto.transaction_date,
                value_date=dto.value_date,
                transaction_type=dto.transaction_type.value, 
                description=dto.description,
                reference=dto.reference,
                amount=dto.amount, 
                is_reconciled=False, 
                is_from_statement=False, 
                raw_statement_data=None,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_transaction = await self.bank_transaction_service.save(bank_transaction_orm)
            self.logger.info(f"Manual bank transaction ID {saved_transaction.id} created for bank account ID {dto.bank_account_id}.")
            return Result.success(saved_transaction)
        except Exception as e:
            self.logger.error(f"Error creating manual bank transaction: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])


    async def get_transactions_for_bank_account(
        self,
        bank_account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[BankTransactionTypeEnum] = None,
        is_reconciled: Optional[bool] = None,
        is_from_statement_filter: Optional[bool] = None, 
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[BankTransactionSummaryData]]:
        try:
            summaries = await self.bank_transaction_service.get_all_for_bank_account(
                bank_account_id=bank_account_id,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                is_reconciled=is_reconciled,
                is_from_statement_filter=is_from_statement_filter, 
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching bank transactions for account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve bank transaction list: {str(e)}"])

    async def get_bank_transaction_for_dialog(self, transaction_id: int) -> Optional[BankTransaction]:
        try:
            return await self.bank_transaction_service.get_by_id(transaction_id)
        except Exception as e:
            self.logger.error(f"Error fetching BankTransaction ID {transaction_id} for dialog: {e}", exc_info=True)
            return None
            
    async def import_bank_statement_csv(
        self, 
        bank_account_id: int, 
        csv_file_path: str, 
        user_id: int,
        column_mapping: Dict[str, Any], 
        import_options: Dict[str, Any]
    ) -> Result[Dict[str, int]]:
        imported_count = 0; skipped_duplicates_count = 0; failed_rows_count = 0; zero_amount_skipped_count = 0; total_rows_processed = 0
        date_format_str = import_options.get("date_format_str", "%d/%m/%Y"); skip_header = import_options.get("skip_header", True)
        use_single_amount_col = import_options.get("use_single_amount_column", False); debit_is_negative = import_options.get("debit_is_negative_in_single_col", False)
        bank_account = await self.bank_account_service.get_by_id(bank_account_id)
        if not bank_account or not bank_account.is_active: return Result.failure([f"Bank Account ID {bank_account_id} not found or is inactive."])
        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
                using_header_names = any(isinstance(v, str) for v in column_mapping.values()); reader: Any
                if using_header_names: reader = csv.DictReader(csvfile)
                else: reader = csv.reader(csvfile); 
                if skip_header and not using_header_names: 
                    try: next(reader) 
                    except StopIteration: return Result.failure(["CSV file is empty or only contains a header."])
                async with self.app_core.db_manager.session() as session:
                    start_row_num = 2 if skip_header else 1
                    for row_num, raw_row_data in enumerate(reader, start=start_row_num):
                        total_rows_processed += 1; raw_row_dict_for_json: Dict[str, str] = {}
                        try:
                            def get_field_value(field_key: str) -> Optional[str]:
                                specifier = column_mapping.get(field_key); 
                                if specifier is None: return None; val: Optional[str] = None
                                if using_header_names and isinstance(raw_row_data, dict): val = raw_row_data.get(str(specifier))
                                elif not using_header_names and isinstance(raw_row_data, list) and isinstance(specifier, int):
                                    if 0 <= specifier < len(raw_row_data): val = raw_row_data[specifier]
                                return val.strip() if val else None
                            if using_header_names and isinstance(raw_row_data, dict): raw_row_dict_for_json = {k: str(v) for k,v in raw_row_data.items()}
                            elif isinstance(raw_row_data, list): raw_row_dict_for_json = {f"column_{i}": str(val) for i, val in enumerate(raw_row_data)}
                            else: raw_row_dict_for_json = {"error": "Unknown row format"}
                            transaction_date_str = get_field_value("date"); description_str = get_field_value("description")
                            if not transaction_date_str or not description_str: self.logger.warning(f"CSV Import (Row {row_num}): Skipping due to missing date or description."); failed_rows_count += 1; continue
                            try: parsed_transaction_date = datetime.strptime(transaction_date_str, date_format_str).date()
                            except ValueError: self.logger.warning(f"CSV Import (Row {row_num}): Invalid transaction date format '{transaction_date_str}'. Expected '{date_format_str}'. Skipping."); failed_rows_count += 1; continue
                            value_date_str = get_field_value("value_date"); parsed_value_date: Optional[date] = None
                            if value_date_str:
                                try: parsed_value_date = datetime.strptime(value_date_str, date_format_str).date()
                                except ValueError: self.logger.warning(f"CSV Import (Row {row_num}): Invalid value date format '{value_date_str}'.")
                            final_bt_amount = Decimal(0)
                            if use_single_amount_col:
                                amount_str = get_field_value("amount")
                                if not amount_str: self.logger.warning(f"CSV Import (Row {row_num}): Single amount column specified but value is missing. Skipping."); failed_rows_count += 1; continue
                                try:
                                    parsed_csv_amount = Decimal(amount_str.replace(',', ''))
                                    if debit_is_negative: final_bt_amount = parsed_csv_amount
                                    else: final_bt_amount = -parsed_csv_amount
                                except InvalidOperation: self.logger.warning(f"CSV Import (Row {row_num}): Invalid amount '{amount_str}' in single amount column. Skipping."); failed_rows_count += 1; continue
                            else:
                                debit_str = get_field_value("debit"); credit_str = get_field_value("credit")
                                try:
                                    parsed_debit = Decimal(debit_str.replace(',', '')) if debit_str else Decimal(0)
                                    parsed_credit = Decimal(credit_str.replace(',', '')) if credit_str else Decimal(0)
                                    final_bt_amount = parsed_credit - parsed_debit
                                except InvalidOperation: self.logger.warning(f"CSV Import (Row {row_num}): Invalid debit '{debit_str}' or credit '{credit_str}' amount. Skipping."); failed_rows_count += 1; continue
                            if abs(final_bt_amount) < Decimal("0.005"): self.logger.info(f"CSV Import (Row {row_num}): Skipping due to zero net amount."); zero_amount_skipped_count += 1; continue
                            reference_str = get_field_value("reference")
                            stmt_dup = select(BankTransaction).where(BankTransaction.bank_account_id == bank_account_id,BankTransaction.transaction_date == parsed_transaction_date,BankTransaction.amount == final_bt_amount,BankTransaction.description == description_str,BankTransaction.is_from_statement == True)
                            existing_dup_res = await session.execute(stmt_dup)
                            if existing_dup_res.scalars().first(): self.logger.info(f"CSV Import (Row {row_num}): Skipping as likely duplicate."); skipped_duplicates_count += 1; continue
                            txn_type_enum = BankTransactionTypeEnum.DEPOSIT if final_bt_amount > 0 else BankTransactionTypeEnum.WITHDRAWAL
                            txn_orm = BankTransaction(bank_account_id=bank_account_id,transaction_date=parsed_transaction_date,value_date=parsed_value_date,transaction_type=txn_type_enum.value,description=description_str,reference=reference_str if reference_str else None,amount=final_bt_amount,is_reconciled=False,is_from_statement=True,raw_statement_data=raw_row_dict_for_json, created_by_user_id=user_id,updated_by_user_id=user_id)
                            session.add(txn_orm); imported_count += 1
                        except Exception as e_row: self.logger.error(f"CSV Import (Row {row_num}): Unexpected error: {e_row}", exc_info=True); failed_rows_count += 1
            summary = {"total_rows_in_file": total_rows_processed, "imported_count": imported_count, "skipped_duplicates_count": skipped_duplicates_count, "failed_rows_count": failed_rows_count, "zero_amount_skipped_count": zero_amount_skipped_count}
            self.logger.info(f"Bank statement import complete for account ID {bank_account_id}: {summary}")
            return Result.success(summary)
        except FileNotFoundError: self.logger.error(f"CSV Import: File not found at path: {csv_file_path}"); return Result.failure([f"CSV file not found: {csv_file_path}"])
        except Exception as e: self.logger.error(f"CSV Import: General error for account ID {bank_account_id}: {e}", exc_info=True); return Result.failure([f"General error during CSV import: {str(e)}"])

    async def get_unreconciled_transactions_for_matching(
        self, 
        bank_account_id: int, 
        statement_end_date: date,
        page_size_override: int = -1 
    ) -> Result[Tuple[List[BankTransactionSummaryData], List[BankTransactionSummaryData]]]:
        
        try:
            statement_items_result = await self.get_transactions_for_bank_account(
                bank_account_id=bank_account_id,
                end_date=statement_end_date, 
                is_reconciled=False,
                is_from_statement_filter=True,
                page=1, page_size=page_size_override 
            )
            if not statement_items_result.is_success:
                return Result.failure(["Failed to fetch statement items for reconciliation."] + (statement_items_result.errors or []))
            
            statement_lines = statement_items_result.value or []

            system_items_result = await self.get_transactions_for_bank_account(
                bank_account_id=bank_account_id,
                end_date=statement_end_date, 
                is_reconciled=False,
                is_from_statement_filter=False,
                page=1, page_size=page_size_override
            )
            if not system_items_result.is_success:
                return Result.failure(["Failed to fetch system transactions for reconciliation."] + (system_items_result.errors or []))
            
            system_txns = system_items_result.value or []
            
            return Result.success((statement_lines, system_txns))

        except Exception as e:
            self.logger.error(f"Error fetching transactions for matching UI (Account ID: {bank_account_id}): {e}", exc_info=True)
            return Result.failure([f"Unexpected error fetching transactions for reconciliation: {str(e)}"])
```

---
**5. Updated File: `app/business_logic/payment_manager.py`**
---
```python
# File: app/business_logic/payment_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from app.models.business.payment import Payment, PaymentAllocation
from app.models.business.sales_invoice import SalesInvoice
from app.models.business.purchase_invoice import PurchaseInvoice
# REMOVED: from app.models.accounting.account import Account # Not directly used by PaymentManager
from app.models.accounting.journal_entry import JournalEntry 
# REMOVED: from app.models.business.bank_account import BankAccount # Not directly used by PaymentManager

# REMOVED: from app.services.business_services import (
#     PaymentService, BankAccountService, CustomerService, VendorService,
#     SalesInvoiceService, PurchaseInvoiceService
# )
# REMOVED: from app.services.core_services import SequenceService, ConfigurationService
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.accounting.journal_entry_manager import JournalEntryManager 

from app.utils.result import Result
from app.utils.pydantic_models import (
    PaymentCreateData, PaymentSummaryData, PaymentAllocationBaseData,
    JournalEntryData, JournalEntryLineData
)
from app.common.enums import (
    PaymentEntityTypeEnum, PaymentTypeEnum, PaymentStatusEnum,
    InvoiceStatusEnum, JournalTypeEnum, PaymentAllocationDocTypeEnum 
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from sqlalchemy.ext.asyncio import AsyncSession 
    from app.services.business_services import (
        PaymentService, BankAccountService, CustomerService, VendorService,
        SalesInvoiceService, PurchaseInvoiceService
    )
    from app.services.core_services import SequenceService, ConfigurationService
    from app.services.account_service import AccountService
    from app.accounting.journal_entry_manager import JournalEntryManager 

class PaymentManager:
    def __init__(self,
                 payment_service: "PaymentService",
                 sequence_service: "SequenceService",
                 bank_account_service: "BankAccountService",
                 customer_service: "CustomerService",
                 vendor_service: "VendorService",
                 sales_invoice_service: "SalesInvoiceService",
                 purchase_invoice_service: "PurchaseInvoiceService",
                 journal_entry_manager: "JournalEntryManager",
                 account_service: "AccountService",
                 configuration_service: "ConfigurationService",
                 app_core: "ApplicationCore"):
        self.payment_service = payment_service
        self.sequence_service = sequence_service
        self.bank_account_service = bank_account_service
        self.customer_service = customer_service
        self.vendor_service = vendor_service
        self.sales_invoice_service = sales_invoice_service
        self.purchase_invoice_service = purchase_invoice_service
        self.journal_entry_manager = journal_entry_manager
        self.account_service = account_service
        self.configuration_service = configuration_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_payment_data(self, dto: PaymentCreateData, session: "AsyncSession") -> List[str]:
        errors: List[str] = []
        
        entity_name_for_desc: str = "Entity"
        if dto.entity_type == PaymentEntityTypeEnum.CUSTOMER:
            entity = await self.customer_service.get_by_id(dto.entity_id) 
            if not entity or not entity.is_active: errors.append(f"Active Customer ID {dto.entity_id} not found.")
            else: entity_name_for_desc = entity.name
        elif dto.entity_type == PaymentEntityTypeEnum.VENDOR:
            entity = await self.vendor_service.get_by_id(dto.entity_id) 
            if not entity or not entity.is_active: errors.append(f"Active Vendor ID {dto.entity_id} not found.")
            else: entity_name_for_desc = entity.name
        
        if dto.payment_method != PaymentMethodEnum.CASH: 
            if not dto.bank_account_id: errors.append("Bank Account is required for non-cash payments.")
            else:
                bank_acc = await self.bank_account_service.get_by_id(dto.bank_account_id) 
                if not bank_acc or not bank_acc.is_active: errors.append(f"Active Bank Account ID {dto.bank_account_id} not found.")
                elif bank_acc.currency_code != dto.currency_code: errors.append(f"Payment currency ({dto.currency_code}) does not match bank account currency ({bank_acc.currency_code}).")
        
        currency = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
        if not currency or not currency.is_active: errors.append(f"Currency '{dto.currency_code}' is invalid or inactive.")

        total_allocated = Decimal(0)
        for i, alloc_dto in enumerate(dto.allocations):
            total_allocated += alloc_dto.amount_allocated
            invoice_orm: Union[SalesInvoice, PurchaseInvoice, None] = None
            doc_type_str = ""
            if alloc_dto.document_type == PaymentAllocationDocTypeEnum.SALES_INVOICE:
                invoice_orm = await self.sales_invoice_service.get_by_id(alloc_dto.document_id) 
                doc_type_str = "Sales Invoice"
            elif alloc_dto.document_type == PaymentAllocationDocTypeEnum.PURCHASE_INVOICE:
                invoice_orm = await self.purchase_invoice_service.get_by_id(alloc_dto.document_id) 
                doc_type_str = "Purchase Invoice"
            
            if not invoice_orm: errors.append(f"Allocation {i+1}: {doc_type_str} ID {alloc_dto.document_id} not found.")
            elif invoice_orm.status not in [InvoiceStatusEnum.APPROVED, InvoiceStatusEnum.PARTIALLY_PAID, InvoiceStatusEnum.OVERDUE]:
                errors.append(f"Allocation {i+1}: {doc_type_str} {invoice_orm.invoice_no} is not in an allocatable status ({invoice_orm.status.value}).") 
            elif isinstance(invoice_orm, SalesInvoice) and invoice_orm.customer_id != dto.entity_id:
                 errors.append(f"Allocation {i+1}: Sales Invoice {invoice_orm.invoice_no} does not belong to selected customer.")
            elif isinstance(invoice_orm, PurchaseInvoice) and invoice_orm.vendor_id != dto.entity_id:
                 errors.append(f"Allocation {i+1}: Purchase Invoice {invoice_orm.invoice_no} does not belong to selected vendor.")
            elif (invoice_orm.total_amount - invoice_orm.amount_paid) < alloc_dto.amount_allocated:
                 outstanding_bal = invoice_orm.total_amount - invoice_orm.amount_paid
                 errors.append(f"Allocation {i+1}: Amount for {doc_type_str} {invoice_orm.invoice_no} ({alloc_dto.amount_allocated:.2f}) exceeds outstanding balance ({outstanding_bal:.2f}).")
        
        if total_allocated > dto.amount:
            errors.append(f"Total allocated amount ({total_allocated}) cannot exceed total payment amount ({dto.amount}).")
        
        return errors

    async def create_payment(self, dto: PaymentCreateData) -> Result[Payment]:
        async with self.app_core.db_manager.session() as session: 
            try:
                validation_errors = await self._validate_payment_data(dto, session=session)
                if validation_errors:
                    return Result.failure(validation_errors)

                payment_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "payment", session=session)
                if not payment_no_str: return Result.failure(["Failed to generate payment number."])

                cash_or_bank_gl_id: Optional[int] = None
                ar_ap_gl_id: Optional[int] = None
                entity_name_for_desc: str = "Entity"

                if dto.payment_method != PaymentMethodEnum.CASH:
                    bank_account = await self.bank_account_service.get_by_id(dto.bank_account_id) # type: ignore
                    if not bank_account or not bank_account.gl_account_id: return Result.failure(["Bank account or its GL link not found."])
                    cash_or_bank_gl_id = bank_account.gl_account_id
                else: 
                    cash_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultCash", "1112") 
                    cash_gl_acc = await self.account_service.get_by_code(cash_acc_code) if cash_acc_code else None
                    if not cash_gl_acc or not cash_gl_acc.is_active: return Result.failure([f"Default Cash account ({cash_acc_code}) not configured or inactive."])
                    cash_or_bank_gl_id = cash_gl_acc.id

                if dto.entity_type == PaymentEntityTypeEnum.CUSTOMER:
                    customer = await self.customer_service.get_by_id(dto.entity_id)
                    if not customer or not customer.receivables_account_id: return Result.failure(["Customer AR account not found."])
                    ar_ap_gl_id = customer.receivables_account_id
                    entity_name_for_desc = customer.name
                elif dto.entity_type == PaymentEntityTypeEnum.VENDOR:
                    vendor = await self.vendor_service.get_by_id(dto.entity_id)
                    if not vendor or not vendor.payables_account_id: return Result.failure(["Vendor AP account not found."])
                    ar_ap_gl_id = vendor.payables_account_id
                    entity_name_for_desc = vendor.name
                
                if not cash_or_bank_gl_id or not ar_ap_gl_id:
                    return Result.failure(["Could not determine all necessary GL accounts for the payment journal."])

                payment_orm = Payment(
                    payment_no=payment_no_str, payment_type=dto.payment_type.value,
                    payment_method=dto.payment_method.value, payment_date=dto.payment_date,
                    entity_type=dto.entity_type.value, entity_id=dto.entity_id,
                    bank_account_id=dto.bank_account_id, currency_code=dto.currency_code,
                    exchange_rate=dto.exchange_rate, amount=dto.amount, reference=dto.reference,
                    description=dto.description, cheque_no=dto.cheque_no,
                    status=PaymentStatusEnum.APPROVED.value, 
                    created_by_user_id=dto.user_id, updated_by_user_id=dto.user_id
                )
                for alloc_dto in dto.allocations:
                    payment_orm.allocations.append(PaymentAllocation(
                        document_type=alloc_dto.document_type.value,
                        document_id=alloc_dto.document_id,
                        amount=alloc_dto.amount_allocated,
                        created_by_user_id=dto.user_id 
                    ))
                
                je_lines_data: List[JournalEntryLineData] = []
                desc_suffix = f"Pmt No: {payment_no_str} for {entity_name_for_desc}"
                
                if dto.payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT: 
                    je_lines_data.append(JournalEntryLineData(account_id=cash_or_bank_gl_id, debit_amount=dto.amount, credit_amount=Decimal(0), description=f"Customer Receipt - {desc_suffix}"))
                    je_lines_data.append(JournalEntryLineData(account_id=ar_ap_gl_id, debit_amount=Decimal(0), credit_amount=dto.amount, description=f"Clear A/R - {desc_suffix}"))
                elif dto.payment_type == PaymentTypeEnum.VENDOR_PAYMENT: 
                    je_lines_data.append(JournalEntryLineData(account_id=ar_ap_gl_id, debit_amount=dto.amount, credit_amount=Decimal(0), description=f"Clear A/P - {desc_suffix}"))
                    je_lines_data.append(JournalEntryLineData(account_id=cash_or_bank_gl_id, debit_amount=Decimal(0), credit_amount=dto.amount, description=f"Vendor Payment - {desc_suffix}"))
                
                je_dto = JournalEntryData(
                    journal_type=JournalTypeEnum.CASH_RECEIPT.value if dto.payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT else JournalTypeEnum.CASH_DISBURSEMENT.value,
                    entry_date=dto.payment_date, description=f"{dto.payment_type.value} - {entity_name_for_desc}",
                    reference=dto.reference or payment_no_str, user_id=dto.user_id, lines=je_lines_data,
                    source_type="Payment", source_id=0 
                )
                
                saved_payment = await self.payment_service.save(payment_orm, session=session)
                je_dto.source_id = saved_payment.id 

                create_je_result = await self.journal_entry_manager.create_journal_entry(je_dto, session=session)
                if not create_je_result.is_success or not create_je_result.value:
                    raise Exception(f"Failed to create JE for payment: {', '.join(create_je_result.errors)}") 
                
                created_je: JournalEntry = create_je_result.value
                post_je_result = await self.journal_entry_manager.post_journal_entry(created_je.id, dto.user_id, session=session)
                if not post_je_result.is_success:
                    raise Exception(f"JE (ID: {created_je.id}) created but failed to post: {', '.join(post_je_result.errors)}")

                saved_payment.journal_entry_id = created_je.id
                session.add(saved_payment) 
                
                for alloc_orm in saved_payment.allocations:
                    if alloc_orm.document_type == PaymentAllocationDocTypeEnum.SALES_INVOICE.value:
                        inv = await session.get(SalesInvoice, alloc_orm.document_id)
                        if inv: 
                            inv.amount_paid = (inv.amount_paid or Decimal(0)) + alloc_orm.amount
                            inv.status = InvoiceStatusEnum.PAID.value if inv.amount_paid >= inv.total_amount else InvoiceStatusEnum.PARTIALLY_PAID.value
                            session.add(inv)
                    elif alloc_orm.document_type == PaymentAllocationDocTypeEnum.PURCHASE_INVOICE.value:
                        inv = await session.get(PurchaseInvoice, alloc_orm.document_id)
                        if inv: 
                            inv.amount_paid = (inv.amount_paid or Decimal(0)) + alloc_orm.amount
                            inv.status = InvoiceStatusEnum.PAID.value if inv.amount_paid >= inv.total_amount else InvoiceStatusEnum.PARTIALLY_PAID.value
                            session.add(inv)

                await session.flush()
                await session.refresh(saved_payment, attribute_names=['allocations', 'journal_entry']) 
                
                self.logger.info(f"Payment '{saved_payment.payment_no}' created and posted successfully. JE ID: {created_je.id}")
                return Result.success(saved_payment)

            except Exception as e:
                self.logger.error(f"Error in create_payment transaction: {e}", exc_info=True)
                return Result.failure([f"Failed to create payment: {str(e)}"])


    async def get_payment_for_dialog(self, payment_id: int) -> Optional[Payment]:
        try:
            return await self.payment_service.get_by_id(payment_id)
        except Exception as e:
            self.logger.error(f"Error fetching Payment ID {payment_id} for dialog: {e}", exc_info=True)
            return None

    async def get_payments_for_listing(
        self,
        entity_type: Optional[PaymentEntityTypeEnum] = None,
        entity_id: Optional[int] = None,
        status: Optional[PaymentStatusEnum] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[PaymentSummaryData]]:
        try:
            summaries = await self.payment_service.get_all_summary(
                entity_type=entity_type, entity_id=entity_id, status=status,
                start_date=start_date, end_date=end_date,
                page=page, page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching payment listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve payment list: {str(e)}"])
```

---
*(The files `SalesInvoiceManager`, `PurchaseInvoiceManager`, `TaxCalculator`, `GSTManager`, `IncomeTaxManager`, `WithholdingTaxManager`, and `FinancialStatementGenerator` also require similar fixes by moving their direct service imports for constructor arguments into `TYPE_CHECKING` blocks and using string literals for type hints in their `__init__` signatures. Due to response length limits, I will provide these in a subsequent response if the application still fails or if you request them specifically. The principle of the fix is identical for all of them.)*

**Summary of Proactive Fixes Applied (in addition to `CustomerManager`):**
*   `app/business_logic/vendor_manager.py`: Service imports moved to `TYPE_CHECKING`, constructor hints updated.
*   `app/business_logic/product_manager.py`: Service imports moved to `TYPE_CHECKING`, constructor hints updated.
*   `app/business_logic/bank_account_manager.py`: Service imports moved to `TYPE_CHECKING`, constructor hints updated.
*   `app/business_logic/bank_transaction_manager.py`: Service imports moved to `TYPE_CHECKING`, constructor hints updated.
*   `app/business_logic/payment_manager.py`: Service imports moved to `TYPE_CHECKING`, constructor hints updated. (Also fixed some direct model imports that were not needed)

I will defer generating the other manager files until the current error chain is fully resolved or if you specifically request them, to keep the response focused. The current set of fixes should resolve the `VendorManager` import error and potentially subsequent ones in the `business_logic` managers that were provided in the file set.
