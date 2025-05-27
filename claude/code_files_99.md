<think>
The application is stable, and the README.md has been updated to reflect the completion of the basic Customer Management module. The user now wants to proceed with a "next step" based on the "Current Focus / Short-term" roadmap I suggested in the updated README.

The suggested short-term roadmap items were:
1.  **Vendor Management**: Basic UI (List, Add, Edit, Toggle Active) similar to Customer Management.
2.  **Product/Service Management**: Basic UI for managing products/services.
3.  **Refine Reporting**: Improve on-screen display (e.g., `QTableView`).
4.  **User and Role Management UI**: UI in Settings.

**Choosing the Next Feature:**

*   **Vendor Management**: This is the direct counterpart to Customer Management. The patterns (DTOs, Service, Manager, TableModel, Dialog, Widget) are already established with Customers, making Vendor Management a very logical and relatively straightforward next step. It fills a symmetrical gap in core business entity management (AP vs. AR).
*   **Product/Service Management**: Also crucial for eventual invoicing, but might involve more complex considerations (inventory vs. non-inventory, links to multiple GL accounts for sales/COGS/inventory).
*   **Refine Reporting**: This is a UI/UX improvement rather than a new core feature set. Important, but perhaps after more data entry modules are in place.
*   **User and Role Management UI**: Important for administration and security, but other data entity management (like Vendors) might be more central to the "bookkeeping" aspect for an MVP.

**Decision:**
Implementing **Vendor Management** is the most aligned with the current momentum and established patterns. It directly mirrors the recently completed Customer Management, allowing for efficient reuse of design and code structures.

**Plan for this Turn: Implement Basic Vendor Management Module**

This will follow the exact same phased approach as Customer Management:
*   **Phase A: Backend for Vendor Management**
    *   A1. Create Pydantic DTOs for Vendor (`VendorBaseData`, `VendorCreateData`, `VendorUpdateData`, `VendorData`, `VendorSummaryData`).
    *   A2. Define `IVendorRepository` Interface.
    *   A3. Implement `VendorService` (in `app/services/business_services.py`).
    *   A4. Create `VendorManager` (in `app/business_logic/vendor_manager.py`).
    *   A5. Integrate into `ApplicationCore`.
*   **Phase B: Frontend UI for Vendor Management**
    *   B1. Create `VendorTableModel`.
    *   B2. Create `VendorDialog`.
    *   B3. Enhance `VendorsWidget` (from stub to functional).

Given the user's directive to proceed step-by-step and provide complete files, I will tackle **Phase A: Backend for Vendor Management** in this turn.

**Detailed Plan & Checklist (Phase A - Vendor Backend):**

**A1. Create Pydantic DTOs for Vendor**
   *   **Goal:** Define DTOs for vendor data.
   *   **File to Update:** `app/utils/pydantic_models.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `VendorBaseData`: Fields analogous to `CustomerBaseData` but for vendors (e.g., `vendor_code`, `name`, `email`, address, payment terms, `currency_code`, `payables_account_id`, `withholding_tax_applicable`, `withholding_tax_rate`).
        *   [ ] Define `VendorCreateData(VendorBaseData, UserAuditData)`.
        *   [ ] Define `VendorUpdateData(VendorBaseData, UserAuditData)` (with `id: int`).
        *   [ ] Define `VendorData(VendorBaseData)` (with `id` and audit timestamps).
        *   [ ] Define `VendorSummaryData(AppBaseModel)` (for list views: `id`, `vendor_code`, `name`, `email`, `phone`, `is_active`).

**A2. Define `IVendorRepository` Interface**
   *   **Goal:** Specify the contract for vendor data access.
   *   **File to Update:** `app/services/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `Vendor` ORM model and `VendorSummaryData` DTO.
        *   [ ] Define `IVendorRepository(IRepository[Vendor, int])`.
        *   [ ] Declare methods: `get_by_code(code: str)`, `get_all_summary(active_only, search_term, page, page_size)`.

**A3. Implement `VendorService`**
   *   **Goal:** Provide data access logic for `Vendor` entities.
   *   **File to Update:** `app/services/business_services.py` (add `VendorService` class here).
   *   **Checklist & Tasks:**
        *   [ ] Create `VendorService(IVendorRepository)`.
        *   [ ] Implement `get_by_id()`: Eager load `currency`, `payables_account`.
        *   [ ] Implement `get_all_summary()`: Similar to `CustomerService.get_all_summary`, returning `List[VendorSummaryData]`.
        *   [ ] Implement `get_by_code()`.
        *   [ ] Implement `save(vendor: Vendor)`.
        *   [ ] Implement `add()`, `update()`, `delete()` (raise `NotImplementedError` for hard delete).

**A4. Create `VendorManager`**
   *   **Goal:** Encapsulate business logic for vendor management.
   *   **New File:** `app/business_logic/vendor_manager.py`.
   *   **Checklist & Tasks:**
        *   [ ] Create `VendorManager(__init__(self, vendor_service: VendorService, account_service: AccountService, currency_service: CurrencyService, app_core: "ApplicationCore"))`.
        *   [ ] Implement methods analogous to `CustomerManager`:
            *   `get_vendor_for_dialog(vendor_id: int)`.
            *   `get_vendors_for_listing(filters) -> Result[List[VendorSummaryData]]`.
            *   `create_vendor(dto: VendorCreateData) -> Result[Vendor]`. (Validate code, payables account, currency).
            *   `update_vendor(vendor_id: int, dto: VendorUpdateData) -> Result[Vendor]`.
            *   `toggle_vendor_active_status(vendor_id: int, user_id: int) -> Result[Vendor]`.

**A5. Integrate into `app/core/application_core.py` and `app/business_logic/__init__.py`**
   *   **Goal:** Make `VendorService` and `VendorManager` accessible.
   *   **File to Update:** `app/core/application_core.py`.
        *   [ ] Import new classes. Add instance variable placeholders. Instantiate in `startup()`. Expose via properties.
   *   **File to Update:** `app/business_logic/__init__.py`.
        *   [ ] Export `VendorManager`.
   *   **File to Update:** `app/services/__init__.py`.
        *   [ ] Export `VendorService` (if defined in `business_services.py`, it will be imported from there) and `IVendorRepository`.

This mirrors the Customer backend implementation closely. I will proceed step-by-step, starting with DTOs.
</think>

Excellent! The application is stable and the Customer Management module's backend and basic UI integration seem to be in good shape.

As per your request to follow the roadmap, implementing **Vendor Management** is indeed the next logical step, as it mirrors the Customer Management functionality and builds upon the patterns we've just established. This will involve creating the backend (DTOs, Service, Manager) and then the frontend (TableModel, Dialog, Widget).

We will start with **Phase A: Backend for Vendor Management**.

---
**A1. Update `app/utils/pydantic_models.py` with Vendor DTOs**

**Goal:** Define Data Transfer Objects for creating, updating, and representing vendor data, including necessary validations.

```python
# app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

class AppBaseModel(BaseModel):
    class Config:
        from_attributes = True 
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None and v.is_finite() else None,
        }
        validate_assignment = True 

class UserAuditData(BaseModel):
    user_id: int

# --- Account Related DTOs (existing) ---
class AccountBaseData(AppBaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    account_type: str 
    sub_type: Optional[str] = Field(None, max_length=30)
    tax_treatment: Optional[str] = Field(None, max_length=20)
    gst_applicable: bool = False
    description: Optional[str] = None
    parent_id: Optional[int] = None
    report_group: Optional[str] = Field(None, max_length=50)
    is_control_account: bool = False
    is_bank_account: bool = False
    opening_balance: Decimal = Field(Decimal(0))
    opening_balance_date: Optional[date] = None
    is_active: bool = True

    @validator('opening_balance', pre=True, always=True)
    def opening_balance_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

class AccountCreateData(AccountBaseData, UserAuditData):
    pass

class AccountUpdateData(AccountBaseData, UserAuditData):
    id: int
    pass

# --- Journal Entry Related DTOs (existing) ---
class JournalEntryLineData(AppBaseModel):
    account_id: int
    description: Optional[str] = Field(None, max_length=200)
    debit_amount: Decimal = Field(Decimal(0))
    credit_amount: Decimal = Field(Decimal(0))
    currency_code: str = Field("SGD", max_length=3) 
    exchange_rate: Decimal = Field(Decimal(1))
    tax_code: Optional[str] = Field(None, max_length=20) 
    tax_amount: Decimal = Field(Decimal(0))
    dimension1_id: Optional[int] = None 
    dimension2_id: Optional[int] = None 

    @validator('debit_amount', 'credit_amount', 'exchange_rate', 'tax_amount', pre=True, always=True)
    def amounts_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

    @root_validator(skip_on_failure=True)
    def check_debit_credit_exclusive(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        debit = values.get('debit_amount', Decimal(0))
        credit = values.get('credit_amount', Decimal(0))
        if debit > Decimal(0) and credit > Decimal(0):
            raise ValueError("Debit and Credit amounts cannot both be positive for a single line.")
        return values

class JournalEntryData(AppBaseModel, UserAuditData):
    journal_type: str 
    entry_date: date
    description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)
    is_recurring: bool = False 
    recurring_pattern_id: Optional[int] = None 
    source_type: Optional[str] = Field(None, max_length=50)
    source_id: Optional[int] = None
    lines: List[JournalEntryLineData]

    @validator('lines')
    def check_lines_not_empty(cls, v: List[JournalEntryLineData]) -> List[JournalEntryLineData]:
        if not v:
            raise ValueError("Journal entry must have at least one line.")
        return v
    
    @root_validator(skip_on_failure=True)
    def check_balanced_entry(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        lines = values.get('lines', [])
        if not lines: return values 
        total_debits = sum(line.debit_amount for line in lines)
        total_credits = sum(line.credit_amount for line in lines)
        if abs(total_debits - total_credits) > Decimal("0.01"): 
            raise ValueError(f"Journal entry must be balanced (Debits: {total_debits}, Credits: {total_credits}).")
        return values

# --- GST Return Related DTOs (existing) ---
class GSTReturnData(AppBaseModel, UserAuditData):
    id: Optional[int] = None 
    return_period: str = Field(..., max_length=20)
    start_date: date; end_date: date
    filing_due_date: Optional[date] = None 
    standard_rated_supplies: Decimal = Field(Decimal(0)); zero_rated_supplies: Decimal = Field(Decimal(0))
    exempt_supplies: Decimal = Field(Decimal(0)); total_supplies: Decimal = Field(Decimal(0)) 
    taxable_purchases: Decimal = Field(Decimal(0)); output_tax: Decimal = Field(Decimal(0))
    input_tax: Decimal = Field(Decimal(0)); tax_adjustments: Decimal = Field(Decimal(0))
    tax_payable: Decimal = Field(Decimal(0)) 
    status: str = Field("Draft", max_length=20) 
    submission_date: Optional[date] = None; submission_reference: Optional[str] = Field(None, max_length=50)
    journal_entry_id: Optional[int] = None; notes: Optional[str] = None

    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 
               'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 
               'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs (existing) ---
class TaxCalculationResultData(AppBaseModel):
    tax_amount: Decimal; tax_account_id: Optional[int] = None; taxable_amount: Decimal
class TransactionLineTaxData(AppBaseModel):
    amount: Decimal; tax_code: Optional[str] = None; account_id: Optional[int] = None; index: int 
class TransactionTaxData(AppBaseModel):
    transaction_type: str; lines: List[TransactionLineTaxData]

# --- Validation Result DTO (existing) ---
class AccountValidationResult(AppBaseModel): is_valid: bool; errors: List[str] = []
class AccountValidator: # (existing logic)
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

# --- Company Setting DTO (existing) ---
class CompanySettingData(AppBaseModel, UserAuditData):
    id: Optional[int] = None; company_name: str = Field(..., max_length=100)
    legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20)
    gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False
    address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50)
    country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None 
    website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None 
    fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31)
    base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50)
    date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs (existing) ---
class FiscalYearCreateData(AppBaseModel, UserAuditData):
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date
    auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start, end = values.get('start_date'), values.get('end_date')
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): 
    id: int; name: str; start_date: date; end_date: date
    period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): 
    id: int; year_name: str; start_date: date; end_date: date
    is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = []

# --- Customer Related DTOs (existing) ---
class CustomerBaseData(AppBaseModel):
    customer_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20)
    gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50)
    country: str = Field("Singapore", max_length=50); credit_terms: int = Field(30, ge=0)
    credit_limit: Optional[Decimal] = Field(None, ge=Decimal(0)); currency_code: str = Field("SGD", min_length=3, max_length=3)
    is_active: bool = True; customer_since: Optional[date] = None; notes: Optional[str] = None
    receivables_account_id: Optional[int] = None
    @validator('credit_limit', pre=True, always=True)
    def credit_limit_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_customer(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if customer is GST registered.")
        return values
class CustomerCreateData(CustomerBaseData, UserAuditData): pass
class CustomerUpdateData(CustomerBaseData, UserAuditData): id: int
class CustomerData(CustomerBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class CustomerSummaryData(AppBaseModel): id: int; customer_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- NEW: Vendor Related DTOs ---
class VendorBaseData(AppBaseModel):
    vendor_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    legal_name: Optional[str] = Field(None, max_length=200)
    uen_no: Optional[str] = Field(None, max_length=20)
    gst_registered: bool = False
    gst_no: Optional[str] = Field(None, max_length=20)
    withholding_tax_applicable: bool = False
    withholding_tax_rate: Optional[Decimal] = Field(None, ge=Decimal(0), le=Decimal(100)) # Percentage
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=50)
    country: str = Field("Singapore", max_length=50)
    payment_terms: int = Field(30, ge=0) # Days
    currency_code: str = Field("SGD", min_length=3, max_length=3)
    is_active: bool = True
    vendor_since: Optional[date] = None
    notes: Optional[str] = None
    bank_account_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    bank_swift_code: Optional[str] = Field(None, max_length=20)
    payables_account_id: Optional[int] = None # Must be an existing 'Liability' type account

    @validator('withholding_tax_rate', pre=True, always=True)
    def wht_rate_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else None

    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
        if values.get('gst_registered') and not values.get('gst_no'):
            raise ValueError("GST No. is required if vendor is GST registered.")
        return values
    
    @root_validator(skip_on_failure=True)
    def check_wht_rate_if_applicable(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('withholding_tax_applicable') and values.get('withholding_tax_rate') is None:
            raise ValueError("Withholding Tax Rate is required if Withholding Tax is applicable.")
        if not values.get('withholding_tax_applicable') and values.get('withholding_tax_rate') is not None:
            # Optionally clear or warn, for now allow rate to be stored but not used
            pass
        return values

class VendorCreateData(VendorBaseData, UserAuditData):
    pass

class VendorUpdateData(VendorBaseData, UserAuditData):
    id: int

class VendorData(VendorBaseData): # For displaying full vendor details
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    updated_by_user_id: int

class VendorSummaryData(AppBaseModel): # For table listings
    id: int
    vendor_code: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool

```
**Validation for `app/utils/pydantic_models.py`:**
*   **New Vendor DTOs Added**:
    *   `VendorBaseData`: Contains common fields from the `Vendor` ORM model, with Pydantic `Field` constraints. Includes fields like `withholding_tax_applicable` and `withholding_tax_rate`.
    *   Added validators for `withholding_tax_rate` (to decimal) and root validators for `check_gst_no_if_registered_vendor` (renamed to avoid conflict with customer's) and `check_wht_rate_if_applicable`.
    *   `VendorCreateData`, `VendorUpdateData`, `VendorData`, `VendorSummaryData`: Defined analogously to Customer DTOs.
*   **Existing DTOs**:
    *   Renamed customer's `check_gst_no_if_registered` root validator to `check_gst_no_if_registered_customer` to avoid potential conflicts if a base class were ever to try and inherit both.
    *   `CompanySettingData`: Default `date_format` was previously changed to `dd/MM/yyyy`, which is fine.
*   No other existing DTOs were unintentionally modified.

This file now correctly includes DTOs for Vendor management.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1NGBX2Et-BABCUeL5QJkhX44BBI0MrYA3/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing

