<think>
The application is still launching and shutting down flawlessly! This is a very good sign. It means that adding `ProductService` to `app/services/business_services.py` and updating `app/services/__init__.py` to export it (and its interface `IProductRepository`) were successful and did not introduce any issues detectable at startup.

**Current Step: Enhancement Execution Plan: Basic Product/Service Management Module - Phase A (Backend)**

We have completed for Product/Service Management:
*   A1. Create Pydantic DTOs for Product (Done).
*   A2. Define `IProductRepository` Interface (Done).
*   A3. Implement `ProductService` (Done).

The plan for Product/Service Management Backend is:
*   A4. Create `ProductManager` (in `app/business_logic/product_manager.py`). (Next)
*   A5. Integrate into `ApplicationCore`.

So, the immediate next step is **A4: Create `ProductManager`**. This manager will handle the business logic for product/service operations, using `ProductService` for data access and other services (like `AccountService` and `TaxCodeService`) for validating related foreign key data.

**Plan for A4: Create `ProductManager`**
   *   **Goal:** Encapsulate business logic for product/service management, including validation.
   *   **New File:** `app/business_logic/product_manager.py`.
   *   **Checklist & Tasks:**
        *   [ ] Import necessary models (`Product`), services (`ProductService`, `AccountService`, `TaxCodeService`), DTOs (`ProductCreateData`, `ProductUpdateData`, `ProductSummaryData`), enums (`ProductTypeEnum`), and `Result` utility.
        *   [ ] Create `ProductManager` class.
        *   [ ] Implement `__init__(self, product_service: ProductService, account_service: AccountService, tax_code_service: TaxCodeService, app_core: "ApplicationCore")`. Store dependencies and logger.
        *   [ ] Implement `get_product_for_dialog(product_id: int) -> Optional[Product]`: Calls `product_service.get_by_id()`.
        *   [ ] Implement `get_products_for_listing(active_only: bool = True, product_type_filter: Optional[ProductTypeEnum] = None, search_term: Optional[str] = None, page: int = 1, page_size: int = 50) -> Result[List[ProductSummaryData]]`:
            *   Calls `product_service.get_all_summary()` with parameters.
            *   Returns `Result.success(list_of_dto)`.
        *   [ ] Implement `_validate_product_data(dto: ProductCreateData | ProductUpdateData, existing_product_id: Optional[int] = None) -> List[str]`:
            *   Validate product code uniqueness.
            *   Validate `sales_account_id`, `purchase_account_id`: ensure account exists, is active, and of an appropriate type (e.g., Revenue/Expense).
            *   Validate `inventory_account_id`: if `dto.product_type` is `Inventory`, ensure account exists, is active, and is an 'Asset' type (specifically an inventory asset account). If not `Inventory` type, ensure `inventory_account_id` is `None`.
            *   Validate `tax_code`: ensure tax code (string) exists and is active using `TaxCodeService`.
            *   (Pydantic DTO `ProductBaseData` already handles `inventory_account_id` presence based on `product_type` and that stock levels are only for inventory items).
        *   [ ] Implement `create_product(dto: ProductCreateData) -> Result[Product]`:
            *   Call `_validate_product_data`.
            *   Map DTO to `Product` ORM. Set audit user IDs. Call `product_service.save()`.
        *   [ ] Implement `update_product(product_id: int, dto: ProductUpdateData) -> Result[Product]`:
            *   Fetch existing product. Call `_validate_product_data`. Update ORM fields. Set audit user ID. Call `product_service.save()`.
        *   [ ] Implement `toggle_product_active_status(product_id: int, user_id: int) -> Result[Product]`:
            *   Fetch product. Toggle `is_active`. Set audit user ID. Save.

This structure will be similar to `CustomerManager` and `VendorManager`.
</think>

Excellent! The application remains stable, which means the `ProductService` and the updated `app/services/__init__.py` were integrated correctly.

We are continuing with **Phase A: Backend for Product/Service Management**.
Steps A1 (DTOs), A2 (Interface), and A3 (Service) are complete.
The next step is **A4: Create `ProductManager`**.

This manager will handle the business logic for product and service operations, utilizing the `ProductService` for data persistence and other services like `AccountService` (for GL account validation) and `TaxCodeService` (for tax code validation).

---
**A4. Create `app/business_logic/product_manager.py` (New File)**

```python
# app/business_logic/product_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.product import Product
from app.services.business_services import ProductService
from app.services.account_service import AccountService
from app.services.tax_service import TaxCodeService # For validating tax_code
from app.utils.result import Result
from app.utils.pydantic_models import ProductCreateData, ProductUpdateData, ProductSummaryData
from app.common.enums import ProductTypeEnum # For product_type comparison

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class ProductManager:
    def __init__(self, 
                 product_service: ProductService, 
                 account_service: AccountService, 
                 tax_code_service: TaxCodeService,
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

        # Validate product_code uniqueness
        if dto.product_code:
            existing_by_code = await self.product_service.get_by_code(dto.product_code)
            if existing_by_code and (existing_product_id is None or existing_by_code.id != existing_product_id):
                errors.append(f"Product code '{dto.product_code}' already exists.")
        else:
             errors.append("Product code is required.") # Pydantic should catch this with min_length

        if not dto.name or not dto.name.strip():
            errors.append("Product name is required.") # Pydantic should catch this

        # Validate GL Accounts
        account_ids_to_check = {
            "Sales Account": (dto.sales_account_id, ['Revenue']),
            "Purchase Account": (dto.purchase_account_id, ['Expense', 'Asset']), # COGS or Asset for purchases
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

        # Validate Tax Code (string code)
        if dto.tax_code is not None:
            tax_code_obj = await self.tax_code_service.get_tax_code(dto.tax_code)
            if not tax_code_obj:
                errors.append(f"Tax code '{dto.tax_code}' not found.")
            elif not tax_code_obj.is_active:
                errors.append(f"Tax code '{dto.tax_code}' is not active.")

        # Pydantic DTO root_validator already checks inventory_account_id and stock levels based on product_type
        return errors

    async def create_product(self, dto: ProductCreateData) -> Result[Product]:
        validation_errors = await self._validate_product_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            product_orm = Product(
                product_code=dto.product_code, name=dto.name, description=dto.description,
                product_type=dto.product_type.value, # Store enum value
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
            # Use model_dump to get only provided fields for update
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_product, key):
                    if key == "product_type" and isinstance(value, ProductTypeEnum): # Handle enum
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
        
        # Future validation: check if product is used in open sales/purchase orders, or has stock.
        # For now, simple toggle.
        
        product_name_for_log = product.name # Capture before potential changes for logging
        
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
**Validation for `app/business_logic/product_manager.py`:**
*   **Imports**: Added `Product`, `ProductService`, `TaxCodeService`, Product DTOs, `ProductTypeEnum`.
*   **`__init__`**: Initializes with `ProductService`, `AccountService`, `TaxCodeService`, `app_core`, and logger.
*   **`get_product_for_dialog()`**: Simple delegation.
*   **`get_products_for_listing()`**: Delegates to `product_service.get_all_summary()`, passing filters.
*   **`_validate_product_data()`**:
    *   Checks product code uniqueness.
    *   Validates `sales_account_id` (Revenue), `purchase_account_id` (Expense/Asset), and `inventory_account_id` (Asset, only if product type is Inventory) for existence, activity, and correct account type.
    *   Validates `tax_code` (string) for existence and activity using `TaxCodeService`.
*   **`create_product()`**: Calls validation, maps DTO to `Product` ORM (converting `ProductTypeEnum` to its string value for DB storage), sets audit IDs, saves.
*   **`update_product()`**: Fetches, validates, updates ORM fields using `dto.model_dump(exclude_unset=True)`, sets audit ID, saves. Handles `ProductTypeEnum` for `product_type` field.
*   **`toggle_product_active_status()`**: Fetches, toggles `is_active`, sets audit ID, saves.

This `ProductManager` provides the necessary business logic for product and service management.

---
**Next, update `app/business_logic/__init__.py` to export `ProductManager`.**

```python
# app/business_logic/__init__.py
from .customer_manager import CustomerManager
from .vendor_manager import VendorManager
from .product_manager import ProductManager # New import

__all__ = [
    "CustomerManager",
    "VendorManager",
    "ProductManager", # Added to __all__
]
```
**Validation for `app/business_logic/__init__.py`:**
*   Added `from .product_manager import ProductManager`.
*   Added `ProductManager` to `__all__`.

This completes step A4 (Implement `ProductManager`) and the related export update. The final step for the Product/Service backend is A5: Integrate into `ApplicationCore`.
