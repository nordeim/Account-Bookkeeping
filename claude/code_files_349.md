<think>
The application launched, dashboard KPIs were fetched, but an `AttributeError` occurred in `DashboardWidget._update_kpi_display_slot`:
`AttributeError: 'DashboardKPIData' object has no attribute 'ar_aging_1_30'. Did you mean: 'ar_aging_31_60'?`

**Error Analysis:**
The traceback clearly indicates that on line 224 of `app/ui/dashboard/dashboard_widget.py`, I'm trying to access `kpi_data_dto.ar_aging_1_30`. The error message suggests that this attribute does not exist on the `DashboardKPIData` object and even helpfully suggests `ar_aging_31_60` as a possible intended attribute.

This means there's a mismatch between the field names I defined in the `DashboardKPIData` Pydantic model and the field names I'm trying to access in the `DashboardWidget`.

**1. Deeply Understand Requirements (Recap of DTO and UI fields):**
*   **`DashboardKPIData` DTO (from my previous update in `response_53`):**
    ```python
    class DashboardKPIData(AppBaseModel):
        # ... existing fields ...
        ar_aging_current: Decimal = Field(Decimal(0)) # e.g. 0-30 days # This is "Current (Not Overdue)"
        ar_aging_31_60: Decimal = Field(Decimal(0))
        ar_aging_61_90: Decimal = Field(Decimal(0))
        ar_aging_91_plus: Decimal = Field(Decimal(0))
        # Missing ar_aging_1_30 here!
        ap_aging_current: Decimal = Field(Decimal(0)) # e.g. 0-30 days
        ap_aging_31_60: Decimal = Field(Decimal(0))
        ap_aging_61_90: Decimal = Field(Decimal(0))
        ap_aging_91_plus: Decimal = Field(Decimal(0))
        # Missing ap_aging_1_30 here!
        total_current_assets: Decimal = Field(Decimal(0))
        total_current_liabilities: Decimal = Field(Decimal(0))
        current_ratio: Optional[Decimal] = None
    ```
*   **`DashboardWidget._update_kpi_display_slot` (from my previous update in `response_53`):**
    ```python
    # AR Aging
    self.ar_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_current, bc_symbol))
    self.ar_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_1_30, bc_symbol)) # <<<< ERROR HERE
    self.ar_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_31_60, bc_symbol))
    # ... and similar for AP ...
    self.ap_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_1_30, bc_symbol)) # <<<< Potential similar error
    ```
*   **Aging Buckets in `CustomerService` and `VendorService` (from my previous update in `response_53`):**
    The aging summary dictionary returned by these services was defined with keys like:
    `"Current"`, `"1-30 Days"`, `"31-60 Days"`, `"61-90 Days"`, `"91+ Days"`.
*   **`DashboardManager` (from my previous update in `response_53`):**
    When populating `DashboardKPIData`, it used:
    ```python
    ar_aging_current=ar_summary.get("Current", Decimal(0)),
    ar_aging_31_60=ar_aging_summary.get("31-60 Days", Decimal(0)), # Skips "1-30 Days"
    # ...
    ap_aging_current=ap_summary.get("Current", Decimal(0)),
    ap_aging_31_60=ap_aging_summary.get("31-60 Days", Decimal(0)), # Skips "1-30 Days"
    ```
    And critically, I added this comment in `DashboardManager`:
    ```python
    # Adding 1-30 days for AR (ensure service provides this key or adjust)
    ar_aging_1_30=ar_aging_summary.get("1-30 Days", Decimal(0)),
    # Adding 1-30 days for AP
    ap_aging_1_30=ap_aging_summary.get("1-30 Days", Decimal(0)),
    ```
    This shows that I intended `DashboardKPIData` to have `ar_aging_1_30` and `ap_aging_1_30`.

**The Mismatch:**
1.  The `DashboardKPIData` DTO definition in `app/utils/pydantic_models.py` is missing the `ar_aging_1_30` and `ap_aging_1_30` fields.
2.  The `DashboardManager` correctly populates these fields in the DTO it *constructs* (because Pydantic allows extra fields by default if not strictly configured against it, or I might have added them to a local copy of the DTO in my thought process but not reflected it in the actual `pydantic_models.py` file I generated).
3.  The `DashboardWidget` then correctly *tries* to access `kpi_data_dto.ar_aging_1_30`, but since it wasn't formally defined in the Pydantic model, Pydantic's `__getattr__` raises an `AttributeError`.

**2. Systematic Diagnosis:**
The error is a clear `AttributeError` due to a missing field in the Pydantic model definition that is being accessed.

**3. Implementation Options Exploration:**
The fix is to make the Pydantic model `DashboardKPIData` consistent with how it's being populated by `DashboardManager` and accessed by `DashboardWidget`.

**Chosen Implementation Strategy:**
Add the missing `ar_aging_1_30` and `ap_aging_1_30` fields to the `DashboardKPIData` Pydantic model definition.

**Detailed Execution Plan & Checklist:**

1.  **Modify `DashboardKPIData` in `app/utils/pydantic_models.py`**:
    *   Checklist:
        *   [X] Locate the `DashboardKPIData` class definition.
        *   [X] Add the field: `ar_aging_1_30: Decimal = Field(Decimal(0))` after `ar_aging_current`.
        *   [X] Add the field: `ap_aging_1_30: Decimal = Field(Decimal(0))` after `ap_aging_current`.

No other files need to be changed for this specific error. `DashboardManager` is already attempting to populate these fields, and `DashboardWidget` is already attempting to access them. The Pydantic model was the missing link.

I will generate the updated `app/utils/pydantic_models.py` file.
</think>

You are absolutely right to point out the `AttributeError`. My apologies, this was an oversight where the `DashboardKPIData` Pydantic model was not updated to include all the aging bucket fields that the `DashboardManager` was populating and the `DashboardWidget` was trying to access.

Specifically, the fields `ar_aging_1_30` and `ap_aging_1_30` (representing the "1-30 Days" overdue bucket) were missing from the `DashboardKPIData` DTO definition, even though the service layer calculates this bucket and the manager attempts to pass it.

**Plan to Fix:**
The fix is straightforward:
1.  Modify the `DashboardKPIData` class in `app/utils/pydantic_models.py` to include the missing fields:
    *   `ar_aging_1_30: Decimal = Field(Decimal(0))`
    *   `ap_aging_1_30: Decimal = Field(Decimal(0))`

This will align the DTO definition with its usage in the manager and UI layers. No other files should need changes for this specific error.

---
**Complete Updated File: `app/utils/pydantic_models.py`**
---
```python
# File: app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum, 
    PaymentAllocationDocTypeEnum, DataChangeTypeEnum
)

class AppBaseModel(BaseModel):
    class Config:
        from_attributes = True 
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None and v.is_finite() else None, 
            EmailStr: lambda v: str(v) if v is not None else None,
        }
        validate_assignment = True 

class UserAuditData(BaseModel):
    user_id: int

# --- Account Related DTOs ---
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
    def opening_balance_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

class AccountCreateData(AccountBaseData, UserAuditData): pass
class AccountUpdateData(AccountBaseData, UserAuditData): id: int

# --- Journal Entry Related DTOs ---
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
    def je_line_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0) 
    @root_validator(skip_on_failure=True)
    def check_je_line_debit_credit_exclusive(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        debit = values.get('debit_amount', Decimal(0)); credit = values.get('credit_amount', Decimal(0))
        if debit > Decimal(0) and credit > Decimal(0): raise ValueError("Debit and Credit amounts cannot both be positive for a single line.")
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
    def check_je_lines_not_empty(cls, v: List[JournalEntryLineData]) -> List[JournalEntryLineData]: 
        if not v: raise ValueError("Journal entry must have at least one line.")
        return v
    @root_validator(skip_on_failure=True)
    def check_je_balanced_entry(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        lines = values.get('lines', []); total_debits = sum(l.debit_amount for l in lines); total_credits = sum(l.credit_amount for l in lines)
        if abs(total_debits - total_credits) > Decimal("0.01"): raise ValueError(f"Journal entry must be balanced (Debits: {total_debits}, Credits: {total_credits}).")
        return values

# --- GST Related DTOs ---
class GSTTransactionLineDetail(AppBaseModel):
    transaction_date: date
    document_no: str 
    entity_name: Optional[str] = None 
    description: str
    account_code: str
    account_name: str
    net_amount: Decimal
    gst_amount: Decimal
    tax_code_applied: Optional[str] = None

class GSTReturnData(AppBaseModel, UserAuditData):
    id: Optional[int] = None
    return_period: str = Field(..., max_length=20)
    start_date: date; end_date: date
    filing_due_date: Optional[date] = None 
    standard_rated_supplies: Decimal = Field(Decimal(0))         
    zero_rated_supplies: Decimal = Field(Decimal(0))             
    exempt_supplies: Decimal = Field(Decimal(0))                 
    total_supplies: Decimal = Field(Decimal(0))                  
    taxable_purchases: Decimal = Field(Decimal(0))               
    output_tax: Decimal = Field(Decimal(0))                      
    input_tax: Decimal = Field(Decimal(0))                       
    tax_adjustments: Decimal = Field(Decimal(0))                 
    tax_payable: Decimal = Field(Decimal(0))                     
    status: str = Field("Draft", max_length=20)
    submission_date: Optional[date] = None
    submission_reference: Optional[str] = Field(None, max_length=50)
    journal_entry_id: Optional[int] = None
    notes: Optional[str] = None
    detailed_breakdown: Optional[Dict[str, List[GSTTransactionLineDetail]]] = Field(None, exclude=True) 

    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 
               'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 
               'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs ---
class TaxCalculationResultData(AppBaseModel): tax_amount: Decimal; tax_account_id: Optional[int] = None; taxable_amount: Decimal
class TransactionLineTaxData(AppBaseModel): amount: Decimal; tax_code: Optional[str] = None; account_id: Optional[int] = None; index: int 
class TransactionTaxData(AppBaseModel): transaction_type: str; lines: List[TransactionLineTaxData]

# --- Validation Result DTO ---
class AccountValidationResult(AppBaseModel): is_valid: bool; errors: List[str] = Field(default_factory=list)
class AccountValidator: 
    def validate_common(self, account_data: AccountBaseData) -> List[str]:
        errors = []; 
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

# --- Company Setting DTO ---
class CompanySettingData(AppBaseModel, UserAuditData): 
    id: Optional[int] = None; company_name: str = Field(..., max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50); country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100); phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None; website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None; fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31); base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50); date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs ---
class FiscalYearCreateData(AppBaseModel, UserAuditData): 
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date; auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_fy_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        start, end = values.get('start_date'), values.get('end_date');
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): id: int; name: str; start_date: date; end_date: date; period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): id: int; year_name: str; start_date: date; end_date: date; is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = Field(default_factory=list)

# --- Customer Related DTOs ---
class CustomerBaseData(AppBaseModel): 
    customer_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); credit_terms: int = Field(30, ge=0); credit_limit: Optional[Decimal] = Field(None, ge=Decimal(0)); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; customer_since: Optional[date] = None; notes: Optional[str] = None; receivables_account_id: Optional[int] = None
    @validator('credit_limit', pre=True, always=True)
    def customer_credit_limit_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None 
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_customer(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if customer is GST registered.")
        return values
class CustomerCreateData(CustomerBaseData, UserAuditData): pass
class CustomerUpdateData(CustomerBaseData, UserAuditData): id: int
class CustomerData(CustomerBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class CustomerSummaryData(AppBaseModel): id: int; customer_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- Vendor Related DTOs ---
class VendorBaseData(AppBaseModel): 
    vendor_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); withholding_tax_applicable: bool = False; withholding_tax_rate: Optional[Decimal] = Field(None, ge=Decimal(0), le=Decimal(100)); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); payment_terms: int = Field(30, ge=0); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; vendor_since: Optional[date] = None; notes: Optional[str] = None; bank_account_name: Optional[str] = Field(None, max_length=100); bank_account_number: Optional[str] = Field(None, max_length=50); bank_name: Optional[str] = Field(None, max_length=100); bank_branch: Optional[str] = Field(None, max_length=100); bank_swift_code: Optional[str] = Field(None, max_length=20); payables_account_id: Optional[int] = None
    @validator('withholding_tax_rate', pre=True, always=True)
    def vendor_wht_rate_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None 
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if vendor is GST registered.")
        return values
    @root_validator(skip_on_failure=True)
    def check_wht_rate_if_applicable_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        if values.get('withholding_tax_applicable') and values.get('withholding_tax_rate') is None: raise ValueError("Withholding Tax Rate is required if Withholding Tax is applicable.")
        return values
class VendorCreateData(VendorBaseData, UserAuditData): pass
class VendorUpdateData(VendorBaseData, UserAuditData): id: int
class VendorData(VendorBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class VendorSummaryData(AppBaseModel): id: int; vendor_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- Product/Service Related DTOs ---
class ProductBaseData(AppBaseModel): 
    product_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); description: Optional[str] = None; product_type: ProductTypeEnum; category: Optional[str] = Field(None, max_length=50); unit_of_measure: Optional[str] = Field(None, max_length=20); barcode: Optional[str] = Field(None, max_length=50); sales_price: Optional[Decimal] = Field(None, ge=Decimal(0)); purchase_price: Optional[Decimal] = Field(None, ge=Decimal(0)); sales_account_id: Optional[int] = None; purchase_account_id: Optional[int] = None; inventory_account_id: Optional[int] = None; tax_code: Optional[str] = Field(None, max_length=20); is_active: bool = True; min_stock_level: Optional[Decimal] = Field(None, ge=Decimal(0)); reorder_point: Optional[Decimal] = Field(None, ge=Decimal(0))     
    @validator('sales_price', 'purchase_price', 'min_stock_level', 'reorder_point', pre=True, always=True)
    def product_decimal_fields(cls, v): return Decimal(str(v)) if v is not None else None
    @root_validator(skip_on_failure=True)
    def check_inventory_fields_product(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        product_type = values.get('product_type')
        if product_type == ProductTypeEnum.INVENTORY:
            if values.get('inventory_account_id') is None: raise ValueError("Inventory Account ID is required for 'Inventory' type products.")
        else: 
            if values.get('inventory_account_id') is not None: raise ValueError("Inventory Account ID should only be set for 'Inventory' type products.")
            if values.get('min_stock_level') is not None or values.get('reorder_point') is not None: raise ValueError("Stock levels are only applicable for 'Inventory' type products.")
        return values
class ProductCreateData(ProductBaseData, UserAuditData): pass
class ProductUpdateData(ProductBaseData, UserAuditData): id: int
class ProductData(ProductBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class ProductSummaryData(AppBaseModel): id: int; product_code: str; name: str; product_type: ProductTypeEnum; sales_price: Optional[Decimal] = None; purchase_price: Optional[Decimal] = None; is_active: bool

# --- Sales Invoice Related DTOs ---
class SalesInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None; description: str = Field(..., min_length=1, max_length=200); quantity: Decimal = Field(..., gt=Decimal(0)); unit_price: Decimal = Field(..., ge=Decimal(0)); discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100)); tax_code: Optional[str] = Field(None, max_length=20); dimension1_id: Optional[int] = None; dimension2_id: Optional[int] = None 
    @validator('quantity', 'unit_price', 'discount_percent', pre=True, always=True)
    def sales_inv_line_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class SalesInvoiceBaseData(AppBaseModel):
    customer_id: int; invoice_date: date; due_date: date; currency_code: str = Field("SGD", min_length=3, max_length=3); exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0)); notes: Optional[str] = None; terms_and_conditions: Optional[str] = None
    @validator('exchange_rate', pre=True, always=True)
    def sales_inv_hdr_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(1)
    @root_validator(skip_on_failure=True)
    def check_due_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        invoice_date, due_date = values.get('invoice_date'), values.get('due_date')
        if invoice_date and due_date and due_date < invoice_date: raise ValueError("Due date cannot be before invoice date.")
        return values
class SalesInvoiceCreateData(SalesInvoiceBaseData, UserAuditData): lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1)
class SalesInvoiceUpdateData(SalesInvoiceBaseData, UserAuditData): id: int; lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1)
class SalesInvoiceData(SalesInvoiceBaseData): id: int; invoice_no: str; subtotal: Decimal; tax_amount: Decimal; total_amount: Decimal; amount_paid: Decimal; status: InvoiceStatusEnum; journal_entry_id: Optional[int] = None; lines: List[SalesInvoiceLineBaseData]; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class SalesInvoiceSummaryData(AppBaseModel): id: int; invoice_no: str; invoice_date: date; due_date: date; customer_name: str; total_amount: Decimal; amount_paid: Decimal; status: InvoiceStatusEnum; currency_code: str

# --- User & Role Management DTOs ---
class RoleData(AppBaseModel): id: int; name: str; description: Optional[str] = None; permission_ids: List[int] = Field(default_factory=list) 
class UserSummaryData(AppBaseModel): id: int; username: str; full_name: Optional[str] = None; email: Optional[EmailStr] = None; is_active: bool; last_login: Optional[datetime] = None; roles: List[str] = Field(default_factory=list) 
class UserRoleAssignmentData(AppBaseModel): role_id: int
class UserBaseData(AppBaseModel): username: str = Field(..., min_length=3, max_length=50); full_name: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; is_active: bool = True
class UserCreateInternalData(UserBaseData): password_hash: str; assigned_roles: List[UserRoleAssignmentData] = Field(default_factory=list)
class UserCreateData(UserBaseData, UserAuditData): 
    password: str = Field(..., min_length=8); confirm_password: str; assigned_role_ids: List[int] = Field(default_factory=list)
    @root_validator(skip_on_failure=True)
    def passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('password'), values.get('confirm_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2: raise ValueError('Passwords do not match')
        return values
class UserUpdateData(UserBaseData, UserAuditData): id: int; assigned_role_ids: List[int] = Field(default_factory=list)
class UserPasswordChangeData(AppBaseModel, UserAuditData): 
    user_id_to_change: int; new_password: str = Field(..., min_length=8); confirm_new_password: str
    @root_validator(skip_on_failure=True)
    def new_passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('new_password'), values.get('confirm_new_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2: raise ValueError('New passwords do not match')
        return values
class RoleCreateData(AppBaseModel): name: str = Field(..., min_length=3, max_length=50); description: Optional[str] = Field(None, max_length=200); permission_ids: List[int] = Field(default_factory=list)
class RoleUpdateData(RoleCreateData): id: int
class PermissionData(AppBaseModel): id: int; code: str; description: Optional[str] = None; module: str

# --- Purchase Invoice Related DTOs ---
class PurchaseInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None; description: str = Field(..., min_length=1, max_length=200); quantity: Decimal = Field(..., gt=Decimal(0)); unit_price: Decimal = Field(..., ge=Decimal(0)); discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100)); tax_code: Optional[str] = Field(None, max_length=20); dimension1_id: Optional[int] = None; dimension2_id: Optional[int] = None
    @validator('quantity', 'unit_price', 'discount_percent', pre=True, always=True)
    def purch_inv_line_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class PurchaseInvoiceBaseData(AppBaseModel):
    vendor_id: int; vendor_invoice_no: Optional[str] = Field(None, max_length=50); invoice_date: date; due_date: date; currency_code: str = Field("SGD", min_length=3, max_length=3); exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0)); notes: Optional[str] = None
    @validator('exchange_rate', pre=True, always=True)
    def purch_inv_hdr_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(1)
    @root_validator(skip_on_failure=True)
    def check_pi_due_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        invoice_date, due_date = values.get('invoice_date'), values.get('due_date')
        if invoice_date and due_date and due_date < invoice_date: raise ValueError("Due date cannot be before invoice date.")
        return values
class PurchaseInvoiceCreateData(PurchaseInvoiceBaseData, UserAuditData): lines: List[PurchaseInvoiceLineBaseData] = Field(..., min_length=1)
class PurchaseInvoiceUpdateData(PurchaseInvoiceBaseData, UserAuditData): id: int; lines: List[PurchaseInvoiceLineBaseData] = Field(..., min_length=1)
class PurchaseInvoiceData(PurchaseInvoiceBaseData): id: int; invoice_no: str; subtotal: Decimal; tax_amount: Decimal; total_amount: Decimal; amount_paid: Decimal; status: InvoiceStatusEnum; journal_entry_id: Optional[int] = None; lines: List[PurchaseInvoiceLineBaseData]; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class PurchaseInvoiceSummaryData(AppBaseModel): id: int; invoice_no: str; vendor_invoice_no: Optional[str] = None; invoice_date: date; vendor_name: str; total_amount: Decimal; status: InvoiceStatusEnum; currency_code: str 

# --- Bank Account DTOs ---
class BankAccountBaseData(AppBaseModel):
    account_name: str = Field(..., min_length=1, max_length=100); account_number: str = Field(..., min_length=1, max_length=50); bank_name: str = Field(..., min_length=1, max_length=100); bank_branch: Optional[str] = Field(None, max_length=100); bank_swift_code: Optional[str] = Field(None, max_length=20); currency_code: str = Field("SGD", min_length=3, max_length=3); opening_balance: Decimal = Field(Decimal(0)); opening_balance_date: Optional[date] = None; gl_account_id: int; is_active: bool = True; description: Optional[str] = None
    @validator('opening_balance', pre=True, always=True)
    def bank_opening_balance_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
    @root_validator(skip_on_failure=True)
    def check_ob_date_if_ob_exists_bank(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        ob = values.get('opening_balance'); ob_date = values.get('opening_balance_date')
        if ob is not None and ob != Decimal(0) and ob_date is None: raise ValueError("Opening Balance Date is required if Opening Balance is not zero.")
        if ob_date is not None and (ob is None or ob == Decimal(0)): values['opening_balance_date'] = None 
        return values
class BankAccountCreateData(BankAccountBaseData, UserAuditData): pass
class BankAccountUpdateData(BankAccountBaseData, UserAuditData): id: int
class BankAccountSummaryData(AppBaseModel): id: int; account_name: str; bank_name: str; account_number: str; currency_code: str; current_balance: Decimal; gl_account_code: Optional[str] = None; gl_account_name: Optional[str] = None; is_active: bool

# --- Bank Transaction DTOs ---
class BankTransactionBaseData(AppBaseModel):
    bank_account_id: int; transaction_date: date; value_date: Optional[date] = None; transaction_type: BankTransactionTypeEnum; description: str = Field(..., min_length=1, max_length=200); reference: Optional[str] = Field(None, max_length=100); amount: Decimal 
    @validator('amount', pre=True, always=True)
    def bank_txn_amount_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
    @root_validator(skip_on_failure=True)
    def check_amount_sign_vs_type_bank_txn(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        amount = values.get('amount'); txn_type = values.get('transaction_type')
        if amount is None or txn_type is None: return values 
        if txn_type in [BankTransactionTypeEnum.DEPOSIT, BankTransactionTypeEnum.INTEREST]:
            if amount < Decimal(0): raise ValueError(f"{txn_type.value} amount must be positive or zero.")
        elif txn_type in [BankTransactionTypeEnum.WITHDRAWAL, BankTransactionTypeEnum.FEE]:
            if amount > Decimal(0): raise ValueError(f"{txn_type.value} amount must be negative or zero.")
        return values
class BankTransactionCreateData(BankTransactionBaseData, UserAuditData): pass
class BankTransactionSummaryData(AppBaseModel): id: int; transaction_date: date; value_date: Optional[date] = None; transaction_type: BankTransactionTypeEnum; description: str; reference: Optional[str] = None; amount: Decimal; is_reconciled: bool = False

# --- Payment DTOs ---
class PaymentAllocationBaseData(AppBaseModel):
    document_id: int; document_type: PaymentAllocationDocTypeEnum; amount_allocated: Decimal = Field(..., gt=Decimal(0))
    @validator('amount_allocated', pre=True, always=True)
    def payment_alloc_amount_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class PaymentBaseData(AppBaseModel):
    payment_type: PaymentTypeEnum; payment_method: PaymentMethodEnum; payment_date: date; entity_type: PaymentEntityTypeEnum; entity_id: int; bank_account_id: Optional[int] = None; currency_code: str = Field(..., min_length=3, max_length=3); exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0)); amount: Decimal = Field(..., gt=Decimal(0)); reference: Optional[str] = Field(None, max_length=100); description: Optional[str] = None; cheque_no: Optional[str] = Field(None, max_length=50)
    @validator('exchange_rate', 'amount', pre=True, always=True)
    def payment_base_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
    @root_validator(skip_on_failure=True)
    def check_bank_account_for_non_cash(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        payment_method = values.get('payment_method'); bank_account_id = values.get('bank_account_id')
        if payment_method != PaymentMethodEnum.CASH and bank_account_id is None: raise ValueError("Bank Account is required for non-cash payment methods.")
        if payment_method == PaymentMethodEnum.CASH and bank_account_id is not None: raise ValueError("Bank Account should not be specified for Cash payment method.")
        return values
class PaymentCreateData(PaymentBaseData, UserAuditData):
    allocations: List[PaymentAllocationBaseData] = Field(default_factory=list)
    @root_validator(skip_on_failure=True)
    def check_total_allocation_vs_payment_amount(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        payment_amount = values.get('amount', Decimal(0)); allocations = values.get('allocations', []); total_allocated = sum(alloc.amount_allocated for alloc in allocations)
        if total_allocated > payment_amount: raise ValueError(f"Total allocated amount ({total_allocated}) cannot exceed payment amount ({payment_amount}).")
        return values
class PaymentSummaryData(AppBaseModel): id: int; payment_no: str; payment_date: date; payment_type: PaymentTypeEnum; payment_method: PaymentMethodEnum; entity_type: PaymentEntityTypeEnum; entity_name: str; amount: Decimal; currency_code: str; status: PaymentStatusEnum

# --- Audit Log DTOs ---
class AuditLogEntryData(AppBaseModel): id: int; timestamp: datetime; username: Optional[str] = "System"; action: str; entity_type: str; entity_id: Optional[int] = None; entity_name: Optional[str] = None; changes_summary: Optional[str] = None; ip_address: Optional[str] = None
class DataChangeHistoryEntryData(AppBaseModel): id: int; changed_at: datetime; table_name: str; record_id: int; field_name: str; old_value: Optional[str] = None; new_value: Optional[str] = None; change_type: DataChangeTypeEnum; changed_by_username: Optional[str] = "System"

# --- Bank Reconciliation DTOs ---
class BankReconciliationBaseData(AppBaseModel):
    bank_account_id: int
    statement_date: date
    statement_ending_balance: Decimal
    calculated_book_balance: Decimal
    reconciled_difference: Decimal
    notes: Optional[str] = None

class BankReconciliationCreateData(BankReconciliationBaseData, UserAuditData):
    pass 

class BankReconciliationData(BankReconciliationBaseData): 
    id: int
    reconciliation_date: datetime 
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    
class BankReconciliationSummaryData(AppBaseModel): 
    id: int
    statement_date: date
    statement_ending_balance: Decimal
    reconciled_difference: Decimal
    reconciliation_date: datetime
    created_by_username: Optional[str] = None


# --- Dashboard DTOs ---
class DashboardKPIData(AppBaseModel):
    kpi_period_description: str
    base_currency: str
    total_revenue_ytd: Decimal = Field(Decimal(0))
    total_expenses_ytd: Decimal = Field(Decimal(0))
    net_profit_ytd: Decimal = Field(Decimal(0))
    current_cash_balance: Decimal = Field(Decimal(0))
    total_outstanding_ar: Decimal = Field(Decimal(0))
    total_outstanding_ap: Decimal = Field(Decimal(0))
    total_ar_overdue: Decimal = Field(Decimal(0)) 
    total_ap_overdue: Decimal = Field(Decimal(0))
    # Fields for AR/AP Aging
    ar_aging_current: Decimal = Field(Decimal(0)) 
    ar_aging_1_30: Decimal = Field(Decimal(0))      # ADDED
    ar_aging_31_60: Decimal = Field(Decimal(0))
    ar_aging_61_90: Decimal = Field(Decimal(0))
    ar_aging_91_plus: Decimal = Field(Decimal(0))
    ap_aging_current: Decimal = Field(Decimal(0)) 
    ap_aging_1_30: Decimal = Field(Decimal(0))      # ADDED
    ap_aging_31_60: Decimal = Field(Decimal(0))
    ap_aging_61_90: Decimal = Field(Decimal(0))
    ap_aging_91_plus: Decimal = Field(Decimal(0))
    # Fields for Current Ratio
    total_current_assets: Decimal = Field(Decimal(0))
    total_current_liabilities: Decimal = Field(Decimal(0))
    current_ratio: Optional[Decimal] = None
```

