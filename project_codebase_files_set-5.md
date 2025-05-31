# app/utils/result.py
```py
# File: app/utils/result.py
# (Content as previously generated, verified)
from typing import TypeVar, Generic, List, Any, Optional

T = TypeVar('T')

class Result(Generic[T]):
    def __init__(self, is_success: bool, value: Optional[T] = None, errors: Optional[List[str]] = None):
        self.is_success = is_success
        self.value = value
        self.errors = errors if errors is not None else []

    @staticmethod
    def success(value: Optional[T] = None) -> 'Result[T]':
        return Result(is_success=True, value=value)

    @staticmethod
    def failure(errors: List[str]) -> 'Result[Any]': 
        return Result(is_success=False, errors=errors)

    def __repr__(self):
        if self.is_success:
            return f"<Result success={True} value='{str(self.value)[:50]}'>"
        else:
            return f"<Result success={False} errors={self.errors}>"

```

# app/utils/__init__.py
```py
# File: app/utils/__init__.py
from .converters import to_decimal
from .formatting import format_currency, format_date, format_datetime
from .json_helpers import json_converter, json_date_hook # Added
from .pydantic_models import (
    AppBaseModel, UserAuditData, 
    AccountBaseData, AccountCreateData, AccountUpdateData,
    JournalEntryLineData, JournalEntryData,
    GSTReturnData, TaxCalculationResultData,
    TransactionLineTaxData, TransactionTaxData,
    AccountValidationResult, AccountValidator, CompanySettingData,
    FiscalYearCreateData, FiscalYearData, FiscalPeriodData # Added Fiscal DTOs
)
from .result import Result
from .sequence_generator import SequenceGenerator
from .validation import is_valid_uen

__all__ = [
    "to_decimal", "format_currency", "format_date", "format_datetime",
    "json_converter", "json_date_hook", # Added
    "AppBaseModel", "UserAuditData", 
    "AccountBaseData", "AccountCreateData", "AccountUpdateData",
    "JournalEntryLineData", "JournalEntryData",
    "GSTReturnData", "TaxCalculationResultData",
    "TransactionLineTaxData", "TransactionTaxData",
    "AccountValidationResult", "AccountValidator", "CompanySettingData",
    "FiscalYearCreateData", "FiscalYearData", "FiscalPeriodData", # Added Fiscal DTOs
    "Result", "SequenceGenerator", "is_valid_uen"
]

```

# app/utils/pydantic_models.py
```py
# File: app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ProductTypeEnum, InvoiceStatusEnum 

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

# --- GST Return Related DTOs ---
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
    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs ---
class TaxCalculationResultData(AppBaseModel): tax_amount: Decimal; tax_account_id: Optional[int] = None; taxable_amount: Decimal
class TransactionLineTaxData(AppBaseModel): amount: Decimal; tax_code: Optional[str] = None; account_id: Optional[int] = None; index: int 
class TransactionTaxData(AppBaseModel): transaction_type: str; lines: List[TransactionLineTaxData]

# --- Validation Result DTO ---
class AccountValidationResult(AppBaseModel): is_valid: bool; errors: List[str] = []
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
class FiscalYearData(AppBaseModel): id: int; year_name: str; start_date: date; end_date: date; is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = []

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
    product_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    product_type: ProductTypeEnum
    category: Optional[str] = Field(None, max_length=50)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    barcode: Optional[str] = Field(None, max_length=50)
    sales_price: Optional[Decimal] = Field(None, ge=Decimal(0))       
    purchase_price: Optional[Decimal] = Field(None, ge=Decimal(0))    
    sales_account_id: Optional[int] = None
    purchase_account_id: Optional[int] = None
    inventory_account_id: Optional[int] = None
    tax_code: Optional[str] = Field(None, max_length=20)
    is_active: bool = True
    min_stock_level: Optional[Decimal] = Field(None, ge=Decimal(0))   
    reorder_point: Optional[Decimal] = Field(None, ge=Decimal(0))     
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
    product_id: Optional[int] = None; description: str = Field(..., min_length=1, max_length=200); quantity: Decimal = Field(..., gt=Decimal(0)); unit_price: Decimal = Field(..., ge=Decimal(0)); discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100)); tax_code: Optional[str] = Field(None, max_length=20)
    dimension1_id: Optional[int] = None 
    dimension2_id: Optional[int] = None 
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
class SalesInvoiceSummaryData(AppBaseModel): id: int; invoice_no: str; invoice_date: date; due_date: date; customer_name: str; total_amount: Decimal; amount_paid: Decimal; status: InvoiceStatusEnum

# --- User & Role Management DTOs ---
class RoleData(AppBaseModel): 
    id: int
    name: str
    description: Optional[str] = None

class UserSummaryData(AppBaseModel): 
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool
    last_login: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list) 

class UserRoleAssignmentData(AppBaseModel): 
    role_id: int

class UserBaseData(AppBaseModel): 
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    is_active: bool = True

class UserCreateInternalData(UserBaseData): 
    password_hash: str 
    assigned_roles: List[UserRoleAssignmentData] = Field(default_factory=list)

class UserCreateData(UserBaseData, UserAuditData): 
    password: str = Field(..., min_length=8)
    confirm_password: str
    assigned_role_ids: List[int] = Field(default_factory=list)

    @root_validator(skip_on_failure=True)
    def passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('password'), values.get('confirm_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('Passwords do not match')
        return values

class UserUpdateData(UserBaseData, UserAuditData): 
    id: int
    assigned_role_ids: List[int] = Field(default_factory=list)

class UserPasswordChangeData(AppBaseModel, UserAuditData): 
    user_id_to_change: int 
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    @root_validator(skip_on_failure=True)
    def new_passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('new_password'), values.get('confirm_new_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('New passwords do not match')
        return values

class RoleCreateData(AppBaseModel): 
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    permission_ids: List[int] = Field(default_factory=list)

class RoleUpdateData(RoleCreateData):
    id: int

class PermissionData(AppBaseModel): 
    id: int
    code: str
    description: Optional[str] = None
    module: str

# --- Purchase Invoice Related DTOs ---
class PurchaseInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None
    description: str = Field(..., min_length=1, max_length=200)
    quantity: Decimal = Field(..., gt=Decimal(0))
    unit_price: Decimal = Field(..., ge=Decimal(0))
    discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100))
    tax_code: Optional[str] = Field(None, max_length=20)
    dimension1_id: Optional[int] = None
    dimension2_id: Optional[int] = None

    @validator('quantity', 'unit_price', 'discount_percent', pre=True, always=True)
    def purch_inv_line_decimals(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

class PurchaseInvoiceBaseData(AppBaseModel):
    vendor_id: int
    vendor_invoice_no: Optional[str] = Field(None, max_length=50) 
    invoice_date: date
    due_date: date
    currency_code: str = Field("SGD", min_length=3, max_length=3)
    exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0))
    notes: Optional[str] = None
    
    @validator('exchange_rate', pre=True, always=True)
    def purch_inv_hdr_decimals(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(1)

    @root_validator(skip_on_failure=True)
    def check_pi_due_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        invoice_date, due_date = values.get('invoice_date'), values.get('due_date')
        if invoice_date and due_date and due_date < invoice_date:
            raise ValueError("Due date cannot be before invoice date.")
        return values

class PurchaseInvoiceCreateData(PurchaseInvoiceBaseData, UserAuditData):
    lines: List[PurchaseInvoiceLineBaseData] = Field(..., min_length=1)

class PurchaseInvoiceUpdateData(PurchaseInvoiceBaseData, UserAuditData):
    id: int
    lines: List[PurchaseInvoiceLineBaseData] = Field(..., min_length=1)

class PurchaseInvoiceData(PurchaseInvoiceBaseData): 
    id: int
    invoice_no: str # Our internal reference number
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    status: InvoiceStatusEnum 
    journal_entry_id: Optional[int] = None
    lines: List[PurchaseInvoiceLineBaseData] 
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    updated_by_user_id: int

class PurchaseInvoiceSummaryData(AppBaseModel): 
    id: int
    invoice_no: str 
    vendor_invoice_no: Optional[str] = None
    invoice_date: date
    vendor_name: str 
    total_amount: Decimal
    status: InvoiceStatusEnum

```

# app/utils/validation.py
```py
# File: app/utils/validation.py
# (Content as previously generated, verified)
def is_valid_uen(uen: str) -> bool:
    if not uen: return True 
    return len(uen) >= 9 and len(uen) <= 10 

```

# app/utils/sequence_generator.py
```py
# File: app/utils/sequence_generator.py
import asyncio
from typing import Optional, TYPE_CHECKING
from app.models.core.sequence import Sequence # Still needed if we fallback or for other methods
from app.services.core_services import SequenceService 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For db_manager access if needed

class SequenceGenerator:
    def __init__(self, sequence_service: SequenceService, app_core_ref: Optional["ApplicationCore"] = None):
        self.sequence_service = sequence_service
        # Store app_core to access db_manager for calling the DB function
        self.app_core = app_core_ref 
        if self.app_core is None and hasattr(sequence_service, 'app_core'): # Fallback if service has it
            self.app_core = sequence_service.app_core


    async def next_sequence(self, sequence_name: str, prefix_override: Optional[str] = None) -> str:
        """
        Generates the next number in a sequence.
        Primarily tries to use the PostgreSQL function core.get_next_sequence_value().
        Falls back to Python-based logic if DB function call fails or app_core is not available for DB manager.
        """
        if self.app_core and hasattr(self.app_core, 'db_manager'):
            try:
                # The DB function `core.get_next_sequence_value(p_sequence_name VARCHAR)`
                # already handles prefix, suffix, formatting and returns the final string.
                # It does NOT take prefix_override. If prefix_override is needed,
                # this DB function strategy needs re-evaluation or the DB func needs an update.
                # For now, assume prefix_override is not used with DB function or is handled by template in DB.
                
                # If prefix_override is essential, we might need to:
                # 1. Modify DB function to accept it.
                # 2. Fetch numeric value from DB, then format in Python with override. (More complex)

                # Current DB function `core.get_next_sequence_value` uses the prefix stored in the table.
                # If prefix_override is provided, the Python fallback might be necessary.
                # Let's assume for now, if prefix_override is given, we must use Python logic.
                
                if prefix_override is None: # Only use DB function if no override, as DB func uses its stored prefix
                    db_func_call = f"SELECT core.get_next_sequence_value('{sequence_name}');"
                    generated_value = await self.app_core.db_manager.execute_scalar(db_func_call) # type: ignore
                    if generated_value:
                        return str(generated_value)
                    else:
                        # Log this failure to use DB func
                        if hasattr(self.app_core.db_manager, 'logger') and self.app_core.db_manager.logger:
                            self.app_core.db_manager.logger.warning(f"DB function core.get_next_sequence_value for '{sequence_name}' returned None. Falling back to Python logic.")
                        else:
                            print(f"Warning: DB function for sequence '{sequence_name}' failed. Falling back.")
                else:
                    if hasattr(self.app_core.db_manager, 'logger') and self.app_core.db_manager.logger:
                        self.app_core.db_manager.logger.info(f"Prefix override for '{sequence_name}' provided. Using Python sequence logic.") # type: ignore
                    else:
                        print(f"Info: Prefix override for '{sequence_name}' provided. Using Python sequence logic.")


            except Exception as e:
                # Log this failure to use DB func
                if hasattr(self.app_core.db_manager, 'logger') and self.app_core.db_manager.logger:
                     self.app_core.db_manager.logger.error(f"Error calling DB sequence function for '{sequence_name}': {e}. Falling back to Python logic.", exc_info=True) # type: ignore
                else:
                    print(f"Error calling DB sequence function for '{sequence_name}': {e}. Falling back.")
        
        # Fallback to Python-based logic (less robust for concurrency)
        sequence_obj = await self.sequence_service.get_sequence_by_name(sequence_name)

        if not sequence_obj:
            # Fallback creation if not found - ensure this is atomic or a rare case
            print(f"Sequence '{sequence_name}' not found in DB, creating with defaults via Python logic.")
            default_actual_prefix = prefix_override if prefix_override is not None else sequence_name.upper()[:3]
            sequence_obj = Sequence(
                sequence_name=sequence_name, next_value=1, increment_by=1,
                min_value=1, max_value=2147483647, prefix=default_actual_prefix,
                format_template=f"{{PREFIX}}-{{VALUE:06d}}" # Ensure d for integer formatting
            )
            # This save should happen in its own transaction managed by sequence_service.
            await self.sequence_service.save_sequence(sequence_obj) 

        current_value = sequence_obj.next_value
        sequence_obj.next_value += sequence_obj.increment_by
        
        if sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            sequence_obj.next_value = sequence_obj.min_value
        elif not sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            # This is a critical error for non-cycling sequences
            raise ValueError(f"Sequence '{sequence_name}' has reached its maximum value ({sequence_obj.max_value}) and cannot cycle.")

        await self.sequence_service.save_sequence(sequence_obj) 

        actual_prefix_for_format = prefix_override if prefix_override is not None else (sequence_obj.prefix or '')
        
        # Refined formatting logic
        template = sequence_obj.format_template
        
        # Handle common padding formats like {VALUE:06} or {VALUE:06d}
        import re
        match = re.search(r"\{VALUE:0?(\d+)[d]?\}", template)
        value_str: str
        if match:
            padding = int(match.group(1))
            value_str = str(current_value).zfill(padding)
            template = template.replace(match.group(0), value_str) # Replace the whole placeholder
        else: # Fallback for simple {VALUE}
            value_str = str(current_value)
            template = template.replace('{VALUE}', value_str)

        template = template.replace('{PREFIX}', actual_prefix_for_format)
        template = template.replace('{SUFFIX}', sequence_obj.suffix or '')
            
        return template

```

# app/utils/formatting.py
```py
# File: app/utils/formatting.py
# (Content as previously generated, verified)
from decimal import Decimal
from datetime import date, datetime

def format_currency(amount: Decimal, currency_code: str = "SGD") -> str:
    return f"{currency_code} {amount:,.2f}"

def format_date(d: date, fmt_str: str = "%d %b %Y") -> str: 
    return d.strftime(fmt_str) 

def format_datetime(dt: datetime, fmt_str: str = "%d %b %Y %H:%M:%S") -> str: 
    return dt.strftime(fmt_str)

```

# app/utils/converters.py
```py
# File: app/utils/converters.py
# (Content as previously generated, verified)
from decimal import Decimal, InvalidOperation

def to_decimal(value: any, default: Decimal = Decimal(0)) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None: 
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError): 
        return default

```

# app/services/journal_service.py
```py
# File: app/services/journal_service.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from datetime import date, datetime, timedelta # Added timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload, joinedload # Added joinedload
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj), 
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.currency),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension1),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension2),
                selectinload(JournalEntry.fiscal_period), 
                selectinload(JournalEntry.created_by_user), 
                selectinload(JournalEntry.updated_by_user)  
            ).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines) 
            ).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_all_summary(self, 
                              start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]:
        async with self.db_manager.session() as session:
            conditions = []
            if start_date_filter:
                conditions.append(JournalEntry.entry_date >= start_date_filter)
            if end_date_filter:
                conditions.append(JournalEntry.entry_date <= end_date_filter)
            if status_filter:
                if status_filter.lower() == "draft":
                    conditions.append(JournalEntry.is_posted == False)
                elif status_filter.lower() == "posted":
                    conditions.append(JournalEntry.is_posted == True)
            if entry_no_filter:
                conditions.append(JournalEntry.entry_no.ilike(f"%{entry_no_filter}%")) 
            if description_filter:
                conditions.append(JournalEntry.description.ilike(f"%{description_filter}%"))
            
            stmt = select(
                JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date,
                JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted,
                func.sum(JournalEntryLine.debit_amount).label("total_debits") # Used for JE list total
            ).join(JournalEntryLine, JournalEntry.id == JournalEntryLine.journal_entry_id, isouter=True)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.group_by(
                JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, 
                JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted
            ).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            
            result = await session.execute(stmt)
            
            summaries: List[Dict[str, Any]] = []
            for row in result.mappings().all(): 
                summaries.append({
                    "id": row.id, "entry_no": row.entry_no, "date": row.entry_date, 
                    "description": row.description, "type": row.journal_type,
                    "total_amount": row.total_debits if row.total_debits is not None else Decimal(0), 
                    "status": "Posted" if row.is_posted else "Draft"
                })
            return summaries
            
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_no == entry_no)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj) 
            ).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.unique().scalars().all())

    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry)
            await session.flush() 
            await session.refresh(journal_entry)
            if journal_entry.lines is not None: 
                await session.refresh(journal_entry, attribute_names=['lines'])
            return journal_entry
            
    async def add(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def update(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entry = await session.get(JournalEntry, id_val)
            if entry:
                if entry.is_posted:
                    self.app_core.logger.warning(f"JournalService: Deletion of posted journal entry ID {id_val} prevented.") # type: ignore
                    return False 
                await session.delete(entry) 
                return True
        return False
    
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc_stmt = select(Account.opening_balance, Account.opening_balance_date).where(Account.id == account_id)
            acc_res = await session.execute(acc_stmt)
            acc_data = acc_res.first()
            
            opening_balance = acc_data.opening_balance if acc_data and acc_data.opening_balance is not None else Decimal(0)
            ob_date = acc_data.opening_balance_date if acc_data and acc_data.opening_balance_date is not None else None

            je_activity_stmt = (
                select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0)))
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date <= as_of_date))
            if ob_date:
                je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            
            result = await session.execute(je_activity_stmt)
            je_net_activity = result.scalar_one_or_none() or Decimal(0)
            return opening_balance + je_net_activity

    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (
                select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0)))
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True,
                    JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date))
            result = await session.execute(stmt)
            balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date) -> List[JournalEntryLine]:
        """ Fetches posted journal lines for a specific account and date range. """
        async with self.db_manager.session() as session:
            stmt = select(JournalEntryLine).options(
                joinedload(JournalEntryLine.journal_entry) # Eager load parent JE for date, no, desc
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)\
            .where(
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no, JournalEntryLine.line_number) # Ensure consistent ordering
            
            result = await session.execute(stmt)
            return list(result.scalars().all()) # .unique() might not be needed if JELine is the primary entity

    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).options(
                joinedload(RecurringPattern.template_journal_entry).selectinload(JournalEntry.lines)
            ).where(
                RecurringPattern.is_active == True,
                RecurringPattern.next_generation_date <= as_of_date,
                or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)
            ).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt)
            return list(result.scalars().unique().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern)
            await session.flush()
            await session.refresh(pattern)
            return pattern

```

# app/services/core_services.py
```py
# File: app/services/core_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import select, update
from app.models.core.sequence import Sequence
from app.models.core.configuration import Configuration
from app.models.core.company_setting import CompanySetting

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class SequenceService:
    def __init__(self, db_manager: "DatabaseManager"):
        self.db_manager = db_manager

    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]:
        async with self.db_manager.session() as session:
            stmt = select(Sequence).where(Sequence.sequence_name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save_sequence(self, sequence_obj: Sequence) -> Sequence:
        async with self.db_manager.session() as session:
            session.add(sequence_obj)
            await session.flush()
            await session.refresh(sequence_obj)
            return sequence_obj

class ConfigurationService:
    def __init__(self, db_manager: "DatabaseManager"):
        self.db_manager = db_manager
    
    async def get_config_by_key(self, key: str) -> Optional[Configuration]:
        async with self.db_manager.session() as session:
            stmt = select(Configuration).where(Configuration.config_key == key)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_config_value(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """Fetches a configuration value by key, returning default if not found."""
        config_entry = await self.get_config_by_key(key)
        if config_entry and config_entry.config_value is not None:
            return config_entry.config_value
        return default_value

    async def save_config(self, config_obj: Configuration) -> Configuration:
        async with self.db_manager.session() as session:
            session.add(config_obj)
            await session.flush()
            await session.refresh(config_obj)
            return config_obj

class CompanySettingsService:
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]:
        async with self.db_manager.session() as session:
            # Ensure eager loading of related user if needed, though not strictly necessary for just settings values
            return await session.get(CompanySetting, settings_id)

    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting:
        if self.app_core and self.app_core.current_user:
            # Assuming updated_by_user_id is the correct attribute name as per model
            settings_obj.updated_by_user_id = self.app_core.current_user.id # type: ignore
        async with self.db_manager.session() as session:
            session.add(settings_obj)
            await session.flush()
            await session.refresh(settings_obj)
            return settings_obj


```

# app/services/__init__.py
```py
# File: app/services/__init__.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Generic, TypeVar, Dict 
from datetime import date
from decimal import Decimal 

T = TypeVar('T') 
ID = TypeVar('ID') 

class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id_val: ID) -> Optional[T]: pass
    @abstractmethod
    async def get_all(self) -> List[T]: pass
    @abstractmethod
    async def add(self, entity: T) -> T: pass
    @abstractmethod
    async def update(self, entity: T) -> T: pass
    @abstractmethod
    async def delete(self, id_val: ID) -> bool: pass

# --- ORM Model Imports ---
from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.tax_code import TaxCode
from app.models.core.company_setting import CompanySetting 
from app.models.accounting.gst_return import GSTReturn
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account_type import AccountType 
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate 
from app.models.core.sequence import Sequence 
from app.models.core.configuration import Configuration 
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice
from app.models.business.purchase_invoice import PurchaseInvoice

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData
)

# --- Enum Imports (for filter types in interfaces) ---
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum


# --- Existing Interfaces (condensed for brevity) ---
class IAccountRepository(IRepository[Account, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]: pass
    @abstractmethod
    async def get_all_active(self) -> List[Account]: pass
    @abstractmethod
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]: pass
    @abstractmethod
    async def save(self, account: Account) -> Account: pass 
    @abstractmethod
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]: pass 
    @abstractmethod
    async def has_transactions(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]: pass

class IJournalEntryRepository(IRepository[JournalEntry, int]): 
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry: pass
    @abstractmethod
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal: pass
    @abstractmethod
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal: pass
    @abstractmethod
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]: pass
    @abstractmethod
    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern: pass
    @abstractmethod
    async def get_all_summary(self, start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]: pass

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): 
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]): 
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]): 
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]): 
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]): 
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): 
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]): 
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]): 
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]): 
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

class ICustomerRepository(IRepository[Customer, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass

class IVendorRepository(IRepository[Vendor, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass

class IProductRepository(IRepository[Product, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None,
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]: pass

class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
    @abstractmethod
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]: pass

class IPurchaseInvoiceRepository(IRepository[PurchaseInvoice, int]):
    @abstractmethod
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: pass 
    
    @abstractmethod
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]: pass
    
    @abstractmethod
    async def get_all_summary(self, 
                              vendor_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[PurchaseInvoiceSummaryData]: pass


# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService 
)

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", "IPurchaseInvoiceRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", "PurchaseInvoiceService", 
]

```

# app/services/accounting_services.py
```py
# File: app/services/accounting_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date
from sqlalchemy import select, and_, or_ # Added or_
from app.models.accounting.account_type import AccountType
from app.models.accounting.currency import Currency
from app.models.accounting.exchange_rate import ExchangeRate
from app.models.accounting.fiscal_year import FiscalYear 
from app.core.database_manager import DatabaseManager
from app.services import (
    IAccountTypeRepository, 
    ICurrencyRepository, 
    IExchangeRateRepository,
    IFiscalYearRepository 
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore


class AccountTypeService(IAccountTypeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            return await session.get(AccountType, id_val)

    async def get_all(self) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).order_by(AccountType.display_order, AccountType.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity) 
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(AccountType, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, name: str) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_category(self, category: str) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.category == category).order_by(AccountType.display_order)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class CurrencyService(ICurrencyRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: str) -> Optional[Currency]:
        async with self.db_manager.session() as session:
            return await session.get(Currency, id_val)

    async def get_all(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                 entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                 entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: str) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(Currency, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_all_active(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).where(Currency.is_active == True).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class ExchangeRateService(IExchangeRateRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            return await session.get(ExchangeRate, id_val)

    async def get_all(self) -> List[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).order_by(ExchangeRate.rate_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def update(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(ExchangeRate, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).where(
                ExchangeRate.from_currency_code == from_code,
                ExchangeRate.to_currency_code == to_code,
                ExchangeRate.rate_date == r_date
            )
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def save(self, entity: ExchangeRate) -> ExchangeRate:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if not entity.id: 
                 if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                    entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

class FiscalYearService(IFiscalYearRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            return await session.get(FiscalYear, id_val)

    async def get_all(self) -> List[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).order_by(FiscalYear.start_date.desc()) 
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)

    async def update(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)
    
    async def save(self, entity: FiscalYear) -> FiscalYear:
        # User audit fields are directly on FiscalYear model and should be set by manager
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        # Implement checks: e.g., cannot delete if periods exist or year is not closed.
        # For MVP, direct delete after confirmation by manager.
        async with self.db_manager.session() as session:
            entity = await session.get(FiscalYear, id_val)
            if entity:
                # Add check for associated fiscal periods
                if entity.fiscal_periods:
                     raise ValueError(f"Cannot delete fiscal year '{entity.year_name}' as it has associated fiscal periods.")
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).where(FiscalYear.year_name == year_name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            conditions = [
                # ExistingStart <= NewEnd AND ExistingEnd >= NewStart
                FiscalYear.start_date <= end_date,
                FiscalYear.end_date >= start_date
            ]
            if exclude_id is not None:
                conditions.append(FiscalYear.id != exclude_id)
            
            stmt = select(FiscalYear).where(and_(*conditions))
            result = await session.execute(stmt)
            return result.scalars().first()

```

# app/services/tax_service.py
```py
# File: app/services/tax_service.py
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import select
from app.models.accounting.tax_code import TaxCode 
from app.models.accounting.gst_return import GSTReturn 
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context
from app.services import ITaxCodeRepository, IGSTReturnRepository 

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class TaxCodeService(ITaxCodeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, id_val: int) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            return await session.get(TaxCode, id_val)
            
    async def get_tax_code(self, code: str) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.code == code, TaxCode.is_active == True)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.is_active == True).order_by(TaxCode.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, entity: TaxCode) -> TaxCode: 
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not entity.id: 
                entity.created_by_user_id = user_id # type: ignore
            entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def add(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)

    async def update(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)
            
    async def delete(self, id_val: int) -> bool: 
        tax_code = await self.get_by_id(id_val)
        if tax_code and tax_code.is_active:
            tax_code.is_active = False
            await self.save(tax_code) 
            return True
        return False

class GSTReturnService(IGSTReturnRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[GSTReturn]:
        async with self.db_manager.session() as session:
            return await session.get(GSTReturn, id_val)

    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]:
        return await self.get_by_id(return_id)

    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not gst_return_data.id:
                gst_return_data.created_by_user_id = user_id # type: ignore
            gst_return_data.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(gst_return_data)
            await session.flush()
            await session.refresh(gst_return_data)
            return gst_return_data
    
    async def get_all(self) -> List[GSTReturn]:
        async with self.db_manager.session() as session:
            stmt = select(GSTReturn).order_by(GSTReturn.end_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def update(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def delete(self, id_val: int) -> bool:
        gst_return = await self.get_by_id(id_val)
        if gst_return and gst_return.status == 'Draft':
            async with self.db_manager.session() as session:
                await session.delete(gst_return)
            return True
        return False

```

# app/services/account_service.py
```py
# File: app/services/account_service.py
# (Content previously updated, ensure imports and UserAuditMixin FKs are handled)
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import select, func, text
from app.models.accounting.account import Account 
from app.models.accounting.journal_entry import JournalEntryLine, JournalEntry 
# from app.core.database_manager import DatabaseManager # Already imported by IAccountRepository context
from app.services import IAccountRepository 
from decimal import Decimal
from datetime import date # Added for type hint in has_transactions

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class AccountService(IAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        async with self.db_manager.session() as session:
            return await session.get(Account, account_id)
    
    async def get_by_code(self, code: str) -> Optional[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code == code)
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def get_all(self) -> List[Account]: 
        async with self.db_manager.session() as session:
            stmt = select(Account).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_active(self) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.is_active == True).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]:
        async with self.db_manager.session() as session:
            conditions = [Account.account_type == account_type]
            if active_only:
                conditions.append(Account.is_active == True)
            
            stmt = select(Account).where(*conditions).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def has_transactions(self, account_id: int) -> bool:
        async with self.db_manager.session() as session:
            stmt_je = select(func.count(JournalEntryLine.id)).join(
                JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
            ).where(
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True
            )
            count_je = (await session.execute(stmt_je)).scalar_one()

            acc = await session.get(Account, account_id)
            has_opening_balance_activity = False
            if acc and acc.opening_balance_date and acc.opening_balance != Decimal(0):
                has_opening_balance_activity = True
            
            return (count_je > 0) or has_opening_balance_activity

    async def save(self, account: Account) -> Account:
        async with self.db_manager.session() as session:
            session.add(account)
            await session.flush() 
            await session.refresh(account)
            return account

    async def add(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def update(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def delete(self, account_id: int) -> bool: 
        raise NotImplementedError("Hard delete of accounts not typically supported. Use deactivation via manager.")
    
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        active_filter_main = "WHERE a.parent_id IS NULL"
        if active_only:
            active_filter_main += " AND a.is_active = TRUE"
        
        active_filter_recursive = ""
        if active_only:
            active_filter_recursive = "AND a.is_active = TRUE"

        query = f"""
            WITH RECURSIVE account_tree_cte AS (
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    0 AS level
                FROM accounting.accounts a
                {active_filter_main}
                
                UNION ALL
                
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    t.level + 1
                FROM accounting.accounts a
                JOIN account_tree_cte t ON a.parent_id = t.id
                WHERE 1=1 {active_filter_recursive} 
            )
            SELECT * FROM account_tree_cte
            ORDER BY account_type, code;
        """
        # Type casting for raw_accounts if execute_query returns list of asyncpg.Record
        raw_accounts: List[Any] = await self.db_manager.execute_query(query)
        accounts_data = [dict(row) for row in raw_accounts]
        
        account_map: Dict[int, Dict[str, Any]] = {account['id']: account for account in accounts_data}
        for account_dict in accounts_data: 
            account_dict['children'] = [] 

        tree_roots: List[Dict[str, Any]] = []
        for account_dict in accounts_data:
            if account_dict['parent_id'] and account_dict['parent_id'] in account_map:
                parent = account_map[account_dict['parent_id']]
                parent['children'].append(account_dict)
            elif not account_dict['parent_id']:
                tree_roots.append(account_dict)
        
        return tree_roots

    async def get_accounts_by_codes(self, codes: List[str]) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code.in_(codes)) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.tax_treatment == tax_treatment_code, Account.is_active == True)
            result = await session.execute(stmt)
            return list(result.scalars().all())

```

# app/services/business_services.py
```py
# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine 
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository 
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData 
)
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum 
from datetime import date 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerService(ICustomerRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).options(selectinload(Customer.currency),selectinload(Customer.receivables_account),selectinload(Customer.created_by_user),selectinload(Customer.updated_by_user)).where(Customer.id == customer_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Customer.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Customer.customer_code.ilike(search_pattern), Customer.name.ilike(search_pattern), Customer.email.ilike(search_pattern) if Customer.email else False )) 
            stmt = select(Customer.id, Customer.customer_code, Customer.name, Customer.email, Customer.phone, Customer.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Customer.name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, customer: Customer) -> Customer:
        async with self.db_manager.session() as session:
            session.add(customer); await session.flush(); await session.refresh(customer); return customer
    async def add(self, entity: Customer) -> Customer: return await self.save(entity)
    async def update(self, entity: Customer) -> Customer: return await self.save(entity)
    async def delete(self, customer_id: int) -> bool:
        log_msg = f"Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")

class VendorService(IVendorRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(selectinload(Vendor.currency), selectinload(Vendor.payables_account),selectinload(Vendor.created_by_user), selectinload(Vendor.updated_by_user)).where(Vendor.id == vendor_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).order_by(Vendor.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[VendorSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Vendor.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Vendor.vendor_code.ilike(search_pattern), Vendor.name.ilike(search_pattern), Vendor.email.ilike(search_pattern) if Vendor.email else False))
            stmt = select(Vendor.id, Vendor.vendor_code, Vendor.name, Vendor.email, Vendor.phone, Vendor.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Vendor.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, vendor: Vendor) -> Vendor:
        async with self.db_manager.session() as session:
            session.add(vendor); await session.flush(); await session.refresh(vendor); return vendor
    async def add(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def update(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def delete(self, vendor_id: int) -> bool:
        log_msg = f"Hard delete attempted for Vendor ID {vendor_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")

class ProductService(IProductRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).options(selectinload(Product.sales_account),selectinload(Product.purchase_account),selectinload(Product.inventory_account),selectinload(Product.tax_code_obj),selectinload(Product.created_by_user),selectinload(Product.updated_by_user)).where(Product.id == product_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).order_by(Product.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,product_type_filter: Optional[ProductTypeEnum] = None,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[ProductSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Product.is_active == True)
            if product_type_filter: conditions.append(Product.product_type == product_type_filter.value)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Product.product_code.ilike(search_pattern), Product.name.ilike(search_pattern), Product.description.ilike(search_pattern) if Product.description else False ))
            stmt = select(Product.id, Product.product_code, Product.name, Product.product_type, Product.sales_price, Product.purchase_price, Product.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Product.product_type, Product.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [ProductSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).where(Product.product_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, product: Product) -> Product:
        async with self.db_manager.session() as session:
            session.add(product); await session.flush(); await session.refresh(product); return product
    async def add(self, entity: Product) -> Product: return await self.save(entity)
    async def update(self, entity: Product) -> Product: return await self.save(entity)
    async def delete(self, product_id: int) -> bool:
        log_msg = f"Hard delete attempted for Product/Service ID {product_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")

class SalesInvoiceService(ISalesInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj),
                selectinload(SalesInvoice.customer), selectinload(SalesInvoice.currency),
                selectinload(SalesInvoice.journal_entry), 
                selectinload(SalesInvoice.created_by_user), selectinload(SalesInvoice.updated_by_user)
            ).where(SalesInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if customer_id is not None: conditions.append(SalesInvoice.customer_id == customer_id)
            if status: conditions.append(SalesInvoice.status == status.value)
            if start_date: conditions.append(SalesInvoice.invoice_date >= start_date)
            if end_date: conditions.append(SalesInvoice.invoice_date <= end_date)
            stmt = select( SalesInvoice.id, SalesInvoice.invoice_no, SalesInvoice.invoice_date, SalesInvoice.due_date,
                Customer.name.label("customer_name"), SalesInvoice.total_amount, SalesInvoice.amount_paid, SalesInvoice.status
            ).join(Customer, SalesInvoice.customer_id == Customer.id) 
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [SalesInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(selectinload(SalesInvoice.lines)).where(SalesInvoice.invoice_no == invoice_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def save(self, invoice: SalesInvoice) -> SalesInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: 
                await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def update(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        log_msg = f"Hard delete attempted for Sales Invoice ID {invoice_id}. Not implemented; use voiding/cancellation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of sales invoices is not supported. Use voiding/cancellation.")

class PurchaseInvoiceService(IPurchaseInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(
                selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product),
                selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.tax_code_obj),
                selectinload(PurchaseInvoice.vendor),
                selectinload(PurchaseInvoice.currency),
                selectinload(PurchaseInvoice.journal_entry),
                selectinload(PurchaseInvoice.created_by_user),
                selectinload(PurchaseInvoice.updated_by_user)
            ).where(PurchaseInvoice.id == invoice_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_summary(self, 
                              vendor_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[PurchaseInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if vendor_id is not None:
                conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            if status:
                conditions.append(PurchaseInvoice.status == status.value)
            if start_date:
                conditions.append(PurchaseInvoice.invoice_date >= start_date)
            if end_date:
                conditions.append(PurchaseInvoice.invoice_date <= end_date)
            
            stmt = select(
                PurchaseInvoice.id, PurchaseInvoice.invoice_no, PurchaseInvoice.vendor_invoice_no, 
                PurchaseInvoice.invoice_date, Vendor.name.label("vendor_name"), 
                PurchaseInvoice.total_amount, PurchaseInvoice.status
            ).join(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            
            if page_size > 0:
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            return [PurchaseInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]

    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(
                selectinload(PurchaseInvoice.lines)
            ).where(PurchaseInvoice.invoice_no == internal_ref_no) 
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(
                selectinload(PurchaseInvoice.lines)
            ).where(
                PurchaseInvoice.vendor_id == vendor_id,
                PurchaseInvoice.vendor_invoice_no == vendor_invoice_no
            )
            result = await session.execute(stmt)
            return result.scalars().first() 

    async def save(self, invoice: PurchaseInvoice) -> PurchaseInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice)
            await session.flush()
            await session.refresh(invoice)
            if invoice.id and invoice.lines:
                await session.refresh(invoice, attribute_names=['lines'])
            return invoice

    async def add(self, entity: PurchaseInvoice) -> PurchaseInvoice:
        return await self.save(entity)

    async def update(self, entity: PurchaseInvoice) -> PurchaseInvoice:
        return await self.save(entity)

    async def delete(self, invoice_id: int) -> bool:
        async with self.db_manager.session() as session:
            pi = await session.get(PurchaseInvoice, invoice_id)
            if pi and pi.status == InvoiceStatusEnum.DRAFT.value: # Only allow deleting drafts
                await session.delete(pi)
                return True
            elif pi:
                # Log or raise specific error that non-drafts cannot be hard-deleted
                self.logger.warning(f"Attempt to delete non-draft Purchase Invoice ID {invoice_id} with status {pi.status}. Denied.")
                raise ValueError(f"Cannot delete Purchase Invoice {pi.invoice_no} as its status is '{pi.status}'. Only Draft invoices can be deleted via this method.")
        return False

```

# app/services/fiscal_period_service.py
```py
# File: app/services/fiscal_period_service.py
# Updated to use FiscalYear model
from typing import List, Optional
from datetime import date
from sqlalchemy import select, extract # Added extract
from app.models.accounting.fiscal_period import FiscalPeriod # Corrected path
from app.models.accounting.fiscal_year import FiscalYear # New import
from app.core.database_manager import DatabaseManager
from app.services import IFiscalPeriodRepository

class FiscalPeriodService(IFiscalPeriodRepository):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_by_id(self, period_id: int) -> Optional[FiscalPeriod]:
        async with self.db_manager.session() as session:
            return await session.get(FiscalPeriod, period_id)

    async def get_all(self) -> List[FiscalPeriod]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalPeriod).order_by(FiscalPeriod.start_date)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalPeriod) -> FiscalPeriod:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: FiscalPeriod) -> FiscalPeriod:
        async with self.db_manager.session() as session:
            session.add(entity) 
            await session.flush()
            await session.refresh(entity)
            return entity
            
    async def delete(self, id_val: int) -> bool:
        period = await self.get_by_id(id_val)
        if period and period.status != 'Archived': 
             async with self.db_manager.session() as session:
                await session.delete(period)
             return True
        return False

    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalPeriod).where(
                FiscalPeriod.start_date <= target_date,
                FiscalPeriod.end_date >= target_date,
                FiscalPeriod.status == 'Open' 
            ).order_by(FiscalPeriod.start_date.desc()) 
            result = await session.execute(stmt)
            return result.scalars().first()
            
    async def get_fiscal_year(self, year_value: int) -> Optional[FiscalYear]: # Changed return type to FiscalYear
        """Gets the FiscalYear ORM object for the specified accounting year (e.g., 2023 for FY2023)."""
        async with self.db_manager.session() as session:
            # Assumes year_name is like "FY2023" or just "2023"
            # This needs a robust way to map an integer year to a FiscalYear record.
            # For now, assuming year_name contains the year as a string.
            # Option 1: year_name is "YYYY"
            # stmt = select(FiscalYear).where(FiscalYear.year_name == str(year_value))
            # Option 2: year_value is contained in year_name
            stmt = select(FiscalYear).where(FiscalYear.year_name.like(f"%{year_value}%")) # type: ignore
            # Option 3: Check if year_value falls within start_date and end_date
            # stmt = select(FiscalYear).where(
            #    extract('year', FiscalYear.start_date) <= year_value,
            #    extract('year', FiscalYear.end_date) >= year_value
            # )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]:
        async with self.db_manager.session() as session:
            conditions = [FiscalPeriod.fiscal_year_id == fiscal_year_id]
            if period_type:
                conditions.append(FiscalPeriod.period_type == period_type)
            stmt = select(FiscalPeriod).where(*conditions).order_by(FiscalPeriod.period_number)
            result = await session.execute(stmt)
            return list(result.scalars().all())

```

