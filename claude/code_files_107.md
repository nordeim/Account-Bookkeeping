<think>
This is excellent! The application launches and shuts down cleanly. The log "INFO - Using compiled Qt resources for VendorsWidget." confirms that the new `VendorsWidget` was initialized successfully, meaning all its backend and UI foundational components (DTOs, Service, Manager, TableModel, Dialog) are correctly integrated at least up to the point of widget instantiation.

**Current Project Status Recap:**

*   **Basic Customer Management Module (Backend & Frontend UI)**: Complete and stable.
*   **Basic Vendor Management Module (Backend & Frontend UI)**: Complete and stable at startup. Functional testing is the next step for this module.
*   All previously implemented features (Settings, CoA, JEs, GST workflow, Financial Reports UI) remain stable.

**Next Step Identification:**

The user requests to "proceed with the next step in your plan."
The "Current Focus / Short-term" roadmap items from the README were:
1.  **Vendor Management**: Basic UI (List, Add, Edit, Toggle Active) similar to Customer Management. (Just completed)
2.  **Product/Service Management**: Basic UI for managing products and services (inventory/non-inventory/service types).
3.  **Refine Reporting**: Improve on-screen display (e.g., `QTableView`).
4.  **User and Role Management UI**: UI in Settings.

Given that Vendor Management is now structurally complete (pending testing), the next most logical feature from this list to build upon the "Business Operations" theme is **Product/Service Management**. This is essential for future invoicing features.

**Plan for this Turn: Implement Basic Product/Service Management Module (Backend First)**

This will follow the same phased approach as Customer and Vendor Management:
*   **Phase A: Backend for Product/Service Management**
    *   A1. Create Pydantic DTOs for Product (`ProductBaseData`, `ProductCreateData`, `ProductUpdateData`, `ProductData`, `ProductSummaryData`).
    *   A2. Define `IProductRepository` Interface.
    *   A3. Implement `ProductService` (in `app/services/business_services.py`).
    *   A4. Create `ProductManager` (in `app/business_logic/product_manager.py`).
    *   A5. Integrate into `ApplicationCore`.
*   **Phase B: Frontend UI for Product/Service Management** (Future turn)
    *   B1. Create `ProductTableModel`.
    *   B2. Create `ProductDialog`.
    *   B3. Enhance `ProductsWidget` (currently a stub if it exists, or create it).

I will start with **Phase A: Backend for Product/Service Management**.

**Detailed Plan & Checklist (Phase A - Product/Service Backend):**

**A1. Create Pydantic DTOs for Product/Service**
   *   **Goal:** Define DTOs for product/service data.
   *   **File to Update:** `app/utils/pydantic_models.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `ProductBaseData`: Fields from `Product` ORM model (e.g., `product_code`, `name`, `description`, `product_type` (Enum: Inventory, Service, Non-Inventory), `category`, `unit_of_measure`, `sales_price`, `purchase_price`, `sales_account_id`, `purchase_account_id`, `inventory_account_id`, `tax_code` (string, maps to TaxCode.code), `is_active`, `min_stock_level`, `reorder_point`).
        *   [ ] Define `ProductCreateData(ProductBaseData, UserAuditData)`.
        *   [ ] Define `ProductUpdateData(ProductBaseData, UserAuditData)` (with `id: int`).
        *   [ ] Define `ProductData(ProductBaseData)` (with `id` and audit timestamps).
        *   [ ] Define `ProductSummaryData(AppBaseModel)` (for list views: `id`, `product_code`, `name`, `product_type`, `sales_price`, `is_active`).

**A2. Define `IProductRepository` Interface**
   *   **Goal:** Specify contract for product/service data access.
   *   **File to Update:** `app/services/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `Product` ORM and `ProductSummaryData` DTO.
        *   [ ] Define `IProductRepository(IRepository[Product, int])`.
        *   [ ] Methods: `get_by_code(code: str)`, `get_all_summary(active_only, product_type_filter, search_term, page, page_size)`.

**A3. Implement `ProductService`**
   *   **Goal:** Data access logic for `Product` entities.
   *   **File to Update:** `app/services/business_services.py` (add `ProductService` class).
   *   **Checklist & Tasks:**
        *   [ ] Create `ProductService(IProductRepository)`.
        *   [ ] `get_by_id()`: Eager load `sales_account`, `purchase_account`, `inventory_account`, `tax_code_obj`.
        *   [ ] `get_all_summary()`: Select summary fields, filter by `active_only`, `product_type`, `search_term`. Paginate. Map to `ProductSummaryData`.
        *   [ ] `get_by_code()`.
        *   [ ] `save(product: Product)`. `add()`, `update()`, `delete()` (NotImplemented).

**A4. Create `ProductManager`**
   *   **Goal:** Business logic for product/service management.
   *   **New File:** `app/business_logic/product_manager.py`.
   *   **Checklist & Tasks:**
        *   [ ] `ProductManager(__init__(self, product_service: ProductService, account_service: AccountService, tax_code_service: TaxCodeService, app_core: "ApplicationCore"))`.
        *   [ ] Methods: `get_product_for_dialog()`, `get_products_for_listing()`, `create_product()`, `update_product()`, `toggle_product_active_status()`.
        *   [ ] Validation in `create/update`: code uniqueness; existence and type of `sales_account_id`, `purchase_account_id`, `inventory_account_id` (e.g., inventory account must be Asset); existence of `tax_code`.

**A5. Integrate into `ApplicationCore`, `app/business_logic/__init__.py`, `app/services/__init__.py`**
   *   **Goal:** Make new components accessible.
   *   **Files to Update:** `app/core/application_core.py`, `app/business_logic/__init__.py`, `app/services/__init__.py`.
   *   **Checklist & Tasks:** Import, add instance vars, instantiate in `startup()`, expose via properties. Export from `__init__` files.

I will start with **A1: Create Pydantic DTOs for Product/Service** by updating `app/utils/pydantic_models.py`.
</think>

This is excellent progress! With the Vendor Management backend successfully integrated and the application remaining stable, we are ready to tackle the next item from your short-term roadmap: **Product/Service Management**.

We will follow the same phased approach: first the backend components (DTOs, Service Interface, Service Implementation, Manager), and then the frontend UI.

**Enhancement Execution Plan: Basic Product/Service Management Module - Phase A (Backend)**

**Overall Objective (Phase A):** Create the backend infrastructure (`IProductRepository` interface, `ProductService` implementation, `ProductManager` business logic) for managing Product and Service data, and integrate these components into the `ApplicationCore`.

---
**A1. Update `app/utils/pydantic_models.py` with Product/Service DTOs**

**Goal:** Define Data Transfer Objects for product/service data, including relevant validations.

```python
# app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ProductTypeEnum # For product_type validation

class AppBaseModel(BaseModel):
    class Config:
        from_attributes = True 
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None and v.is_finite() else None,
        }
        validate_assignment = True 

class UserAuditData(BaseModel):
    user_id: int

# --- Account Related DTOs (existing, condensed for brevity) ---
class AccountBaseData(AppBaseModel): # ...
    code: str = Field(..., max_length=20); name: str = Field(..., max_length=100); account_type: str 
    sub_type: Optional[str] = Field(None, max_length=30); tax_treatment: Optional[str] = Field(None, max_length=20)
    gst_applicable: bool = False; description: Optional[str] = None; parent_id: Optional[int] = None
    report_group: Optional[str] = Field(None, max_length=50); is_control_account: bool = False
    is_bank_account: bool = False; opening_balance: Decimal = Field(Decimal(0))
    opening_balance_date: Optional[date] = None; is_active: bool = True
    @validator('opening_balance', pre=True, always=True)
    def opening_balance_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class AccountCreateData(AccountBaseData, UserAuditData): pass
class AccountUpdateData(AccountBaseData, UserAuditData): id: int

# --- Journal Entry Related DTOs (existing, condensed) ---
class JournalEntryLineData(AppBaseModel): # ...
    account_id: int; description: Optional[str] = Field(None, max_length=200); debit_amount: Decimal = Field(Decimal(0))
    credit_amount: Decimal = Field(Decimal(0)); currency_code: str = Field("SGD", max_length=3) 
    exchange_rate: Decimal = Field(Decimal(1)); tax_code: Optional[str] = Field(None, max_length=20) 
    tax_amount: Decimal = Field(Decimal(0)); dimension1_id: Optional[int] = None; dimension2_id: Optional[int] = None 
    @validator('debit_amount', 'credit_amount', 'exchange_rate', 'tax_amount', pre=True, always=True)
    def je_line_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0) # Renamed validator
    @root_validator(skip_on_failure=True)
    def check_je_line_debit_credit_exclusive(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
        debit = values.get('debit_amount', Decimal(0)); credit = values.get('credit_amount', Decimal(0))
        if debit > Decimal(0) and credit > Decimal(0): raise ValueError("Debit and Credit amounts cannot both be positive for a single line.")
        return values
class JournalEntryData(AppBaseModel, UserAuditData): # ...
    journal_type: str; entry_date: date; description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100); is_recurring: bool = False 
    recurring_pattern_id: Optional[int] = None; source_type: Optional[str] = Field(None, max_length=50)
    source_id: Optional[int] = None; lines: List[JournalEntryLineData]
    @validator('lines')
    def check_je_lines_not_empty(cls, v: List[JournalEntryLineData]) -> List[JournalEntryLineData]: # Renamed validator
        if not v: raise ValueError("Journal entry must have at least one line.")
        return v
    @root_validator(skip_on_failure=True)
    def check_je_balanced_entry(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
        lines = values.get('lines', []); total_debits = sum(l.debit_amount for l in lines); total_credits = sum(l.credit_amount for l in lines)
        if abs(total_debits - total_credits) > Decimal("0.01"): raise ValueError(f"Journal entry must be balanced (Debits: {total_debits}, Credits: {total_credits}).")
        return values

# --- GST Return Related DTOs (existing, condensed) ---
class GSTReturnData(AppBaseModel, UserAuditData): # ... (fields as before)
    id: Optional[int] = None; return_period: str = Field(..., max_length=20); start_date: date; end_date: date; filing_due_date: Optional[date] = None 
    standard_rated_supplies: Decimal = Field(Decimal(0)); zero_rated_supplies: Decimal = Field(Decimal(0)); exempt_supplies: Decimal = Field(Decimal(0)); total_supplies: Decimal = Field(Decimal(0)) 
    taxable_purchases: Decimal = Field(Decimal(0)); output_tax: Decimal = Field(Decimal(0)); input_tax: Decimal = Field(Decimal(0)); tax_adjustments: Decimal = Field(Decimal(0)); tax_payable: Decimal = Field(Decimal(0)) 
    status: str = Field("Draft", max_length=20); submission_date: Optional[date] = None; submission_reference: Optional[str] = Field(None, max_length=50); journal_entry_id: Optional[int] = None; notes: Optional[str] = None
    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs (existing, condensed) ---
class TaxCalculationResultData(AppBaseModel): tax_amount: Decimal; tax_account_id: Optional[int] = None; taxable_amount: Decimal
class TransactionLineTaxData(AppBaseModel): amount: Decimal; tax_code: Optional[str] = None; account_id: Optional[int] = None; index: int 
class TransactionTaxData(AppBaseModel): transaction_type: str; lines: List[TransactionLineTaxData]

# --- Validation Result DTO (existing, condensed) ---
class AccountValidationResult(AppBaseModel): is_valid: bool; errors: List[str] = []
class AccountValidator: # ... (existing logic)
    def validate_common(self, account_data: AccountBaseData) -> List[str]:
        errors = []; errors = []
        if not account_data.code: errors.append("Account code is required.")
        if not account_data.name: errors.append("Account name is required.")
        if not account_data.account_type: errors.append("Account type is required.")
        if account_data.is_bank_account and account_data.account_type != 'Asset': errors.append("Bank accounts must be of type 'Asset'.")
        if account_data.opening_balance_date and account_data.opening_balance == Decimal(0): errors.append("Opening balance date provided but opening balance is zero.")
        if account_data.opening_balance != Decimal(0) and not account_data.opening_balance_date: errors.append("Opening balance provided but opening balance date is missing.")
        return errors
    def validate_create(self, account_data: AccountCreateData) -> AccountValidationResult:
        errors = self.validate_common(account_data); return AccountValidationResult(is_valid=not errors, errors=errors)
    def validate_update(self, account_data: AccountUpdateData) -> AccountValidationResult:
        errors = self.validate_common(account_data)
        if not account_data.id: errors.append("Account ID is required for updates.")
        return AccountValidationResult(is_valid=not errors, errors=errors)

# --- Company Setting DTO (existing, condensed) ---
class CompanySettingData(AppBaseModel, UserAuditData): # ... (fields as before)
    id: Optional[int] = None; company_name: str = Field(..., max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50); country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100); phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None; website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None; fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31); base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50); date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs (existing, condensed) ---
class FiscalYearCreateData(AppBaseModel, UserAuditData): # ... (fields as before)
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date; auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_fy_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
        start, end = values.get('start_date'), values.get('end_date');
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): id: int; name: str; start_date: date; end_date: date; period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): id: int; year_name: str; start_date: date; end_date: date; is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = []

# --- Customer Related DTOs (existing, condensed) ---
class CustomerBaseData(AppBaseModel): # ... (fields as before)
    customer_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); credit_terms: int = Field(30, ge=0); credit_limit: Optional[Decimal] = Field(None, ge=Decimal(0)); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; customer_since: Optional[date] = None; notes: Optional[str] = None; receivables_account_id: Optional[int] = None
    @validator('credit_limit', pre=True, always=True)
    def customer_credit_limit_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None # Renamed validator
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_customer(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if customer is GST registered.")
        return values
class CustomerCreateData(CustomerBaseData, UserAuditData): pass
class CustomerUpdateData(CustomerBaseData, UserAuditData): id: int
class CustomerData(CustomerBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class CustomerSummaryData(AppBaseModel): id: int; customer_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- Vendor Related DTOs (existing, condensed) ---
class VendorBaseData(AppBaseModel): # ... (fields as before)
    vendor_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); withholding_tax_applicable: bool = False; withholding_tax_rate: Optional[Decimal] = Field(None, ge=Decimal(0), le=Decimal(100)); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); payment_terms: int = Field(30, ge=0); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; vendor_since: Optional[date] = None; notes: Optional[str] = None; bank_account_name: Optional[str] = Field(None, max_length=100); bank_account_number: Optional[str] = Field(None, max_length=50); bank_name: Optional[str] = Field(None, max_length=100); bank_branch: Optional[str] = Field(None, max_length=100); bank_swift_code: Optional[str] = Field(None, max_length=20); payables_account_id: Optional[int] = None
    @validator('withholding_tax_rate', pre=True, always=True)
    def vendor_wht_rate_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None # Renamed validator
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if vendor is GST registered.")
        return values
    @root_validator(skip_on_failure=True)
    def check_wht_rate_if_applicable_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
        if values.get('withholding_tax_applicable') and values.get('withholding_tax_rate') is None: raise ValueError("Withholding Tax Rate is required if Withholding Tax is applicable.")
        return values
class VendorCreateData(VendorBaseData, UserAuditData): pass
class VendorUpdateData(VendorBaseData, UserAuditData): id: int
class VendorData(VendorBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class VendorSummaryData(AppBaseModel): id: int; vendor_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- NEW: Product/Service Related DTOs ---
class ProductBaseData(AppBaseModel):
    product_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    product_type: ProductTypeEnum # Use the Enum for validation
    category: Optional[str] = Field(None, max_length=50)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    barcode: Optional[str] = Field(None, max_length=50)
    
    sales_price: Optional[Decimal] = Field(None, ge=Decimal(0))
    purchase_price: Optional[Decimal] = Field(None, ge=Decimal(0))
    
    sales_account_id: Optional[int] = None
    purchase_account_id: Optional[int] = None
    inventory_account_id: Optional[int] = None # Required if product_type is 'Inventory'
    
    tax_code: Optional[str] = Field(None, max_length=20) # This will store TaxCode.code
    is_active: bool = True
    
    min_stock_level: Optional[Decimal] = Field(None, ge=Decimal(0)) # Applicable for 'Inventory' type
    reorder_point: Optional[Decimal] = Field(None, ge=Decimal(0))   # Applicable for 'Inventory' type

    @validator('sales_price', 'purchase_price', 'min_stock_level', 'reorder_point', pre=True, always=True)
    def product_decimal_fields(cls, v):
        return Decimal(str(v)) if v is not None else None

    @root_validator(skip_on_failure=True)
    def check_inventory_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        product_type = values.get('product_type')
        if product_type == ProductTypeEnum.INVENTORY:
            if values.get('inventory_account_id') is None:
                raise ValueError("Inventory Account ID is required for 'Inventory' type products.")
        else: # Service or Non-Inventory
            if values.get('inventory_account_id') is not None:
                raise ValueError("Inventory Account ID should only be set for 'Inventory' type products.")
            if values.get('min_stock_level') is not None or values.get('reorder_point') is not None:
                raise ValueError("Stock levels (min_stock_level, reorder_point) are only applicable for 'Inventory' type products.")
        return values

class ProductCreateData(ProductBaseData, UserAuditData):
    pass

class ProductUpdateData(ProductBaseData, UserAuditData):
    id: int

class ProductData(ProductBaseData): # For displaying full product details
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    updated_by_user_id: int
    # Potentially include names of related accounts/tax_code if needed for display
    # sales_account_name: Optional[str] = None 
    # tax_code_description: Optional[str] = None

class ProductSummaryData(AppBaseModel): # For table listings
    id: int
    product_code: str
    name: str
    product_type: ProductTypeEnum
    sales_price: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None
    is_active: bool

```
**Validation for `app/utils/pydantic_models.py`:**
*   **Import `ProductTypeEnum`**: Added `from app.common.enums import ProductTypeEnum`.
*   **New Product DTOs Added**:
    *   `ProductBaseData`: Includes fields from `Product` ORM model.
        *   `product_type` uses `ProductTypeEnum` for validation.
        *   `sales_price`, `purchase_price`, `min_stock_level`, `reorder_point` are validated to be non-negative `Decimal`s if provided.
        *   A root validator `check_inventory_fields` ensures:
            *   `inventory_account_id` is required if `product_type` is `Inventory`.
            *   `inventory_account_id` is *not* set if `product_type` is not `Inventory`.
            *   `min_stock_level` and `reorder_point` are only applicable for `Inventory` type.
    *   `ProductCreateData(ProductBaseData, UserAuditData)`.
    *   `ProductUpdateData(ProductBaseData, UserAuditData)` with `id: int`.
    *   `ProductData(ProductBaseData)` for full representation.
    *   `ProductSummaryData` for list views.
*   **Existing DTOs**: Renamed some internal Pydantic validators (e.g., `check_je_line_debit_credit_exclusive`) to be more specific to their DTOs to avoid potential name clashes if these DTOs were ever part of a larger hierarchy or union where validator names might collide. This is a proactive minor refinement.
*   No other DTOs were unintentionally modified.

The DTOs for Product/Service management are now defined. The next step is A2: Define `IProductRepository` Interface.
