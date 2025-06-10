# app/utils/json_helpers.py
```py
# File: app/utils/json_helpers.py
import json
from decimal import Decimal
from datetime import date, datetime

def json_converter(obj):
    """Custom JSON converter to handle Decimal and date/datetime objects."""
    if isinstance(obj, Decimal):
        return str(obj)  # Serialize Decimal as string
    if isinstance(obj, (datetime, date)): # Handle both datetime and date
        return obj.isoformat()  # Serialize date/datetime as ISO string
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def json_date_hook(dct):
    """
    Custom object_hook for json.loads to convert ISO date/datetime strings back to objects.
    More specific field name checks might be needed for robustness.
    """
    for k, v in dct.items():
        if isinstance(v, str):
            # Attempt to parse common date/datetime field names
            if k.endswith('_at') or k.endswith('_date') or k in [
                'date', 'start_date', 'end_date', 'closed_date', 'submission_date', 
                'issue_date', 'payment_date', 'last_reconciled_date', 
                'customer_since', 'vendor_since', 'opening_balance_date', 
                'movement_date', 'transaction_date', 'value_date', 
                'invoice_date', 'due_date', 'filing_due_date', 'rate_date',
                'last_login_attempt', 'last_login' # From User model
            ]:
                try:
                    # Try datetime first, then date
                    dt_val = datetime.fromisoformat(v.replace('Z', '+00:00'))
                    # If it has no time component, and field implies date only, convert to date
                    if dt_val.time() == datetime.min.time() and not k.endswith('_at') and k != 'closed_date' and k != 'last_login_attempt' and k != 'last_login': # Heuristic
                         dct[k] = dt_val.date()
                    else:
                        dct[k] = dt_val
                except ValueError:
                    try:
                        dct[k] = python_date.fromisoformat(v)
                    except ValueError:
                        pass # Keep as string if not valid ISO date/datetime
    return dct

```

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
from .json_helpers import json_converter, json_date_hook
from .pydantic_models import (
    AppBaseModel, UserAuditData, 
    AccountBaseData, AccountCreateData, AccountUpdateData,
    JournalEntryLineData, JournalEntryData,
    GSTReturnData, TaxCalculationResultData, GSTTransactionLineDetail,
    TransactionLineTaxData, TransactionTaxData,
    AccountValidationResult, AccountValidator, CompanySettingData,
    FiscalYearCreateData, FiscalYearData, FiscalPeriodData,
    CustomerBaseData, CustomerCreateData, CustomerUpdateData, CustomerSummaryData, CustomerData,
    VendorBaseData, VendorCreateData, VendorUpdateData, VendorSummaryData, VendorData,
    ProductBaseData, ProductCreateData, ProductUpdateData, ProductSummaryData, ProductData,
    SalesInvoiceLineBaseData, SalesInvoiceBaseData, SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceData, SalesInvoiceSummaryData,
    RoleData, UserSummaryData, UserRoleAssignmentData, UserBaseData, UserCreateInternalData, UserCreateData, UserUpdateData, UserPasswordChangeData,
    RoleCreateData, RoleUpdateData, PermissionData,
    PurchaseInvoiceLineBaseData, PurchaseInvoiceBaseData, PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceData, PurchaseInvoiceSummaryData,
    BankAccountBaseData, BankAccountCreateData, BankAccountUpdateData, BankAccountSummaryData,
    BankTransactionBaseData, BankTransactionCreateData, BankTransactionSummaryData,
    PaymentAllocationBaseData, PaymentBaseData, PaymentCreateData, PaymentSummaryData,
    AuditLogEntryData, DataChangeHistoryEntryData,
    BankReconciliationBaseData, BankReconciliationCreateData, BankReconciliationData,
    BankReconciliationSummaryData,
    DashboardKPIData,
    CSVImportErrorData
)
from .result import Result
from .sequence_generator import SequenceGenerator
from .validation import is_valid_uen

__all__ = [
    "to_decimal", "format_currency", "format_date", "format_datetime",
    "json_converter", "json_date_hook",
    "AppBaseModel", "UserAuditData", 
    "AccountBaseData", "AccountCreateData", "AccountUpdateData",
    "JournalEntryLineData", "JournalEntryData",
    "GSTReturnData", "TaxCalculationResultData", "GSTTransactionLineDetail",
    "TransactionLineTaxData", "TransactionTaxData",
    "AccountValidationResult", "AccountValidator", "CompanySettingData",
    "FiscalYearCreateData", "FiscalYearData", "FiscalPeriodData",
    "CustomerBaseData", "CustomerCreateData", "CustomerUpdateData", "CustomerSummaryData", "CustomerData",
    "VendorBaseData", "VendorCreateData", "VendorUpdateData", "VendorSummaryData", "VendorData",
    "ProductBaseData", "ProductCreateData", "ProductUpdateData", "ProductSummaryData", "ProductData",
    "SalesInvoiceLineBaseData", "SalesInvoiceBaseData", "SalesInvoiceCreateData", "SalesInvoiceUpdateData", "SalesInvoiceData", "SalesInvoiceSummaryData",
    "RoleData", "UserSummaryData", "UserRoleAssignmentData", "UserBaseData", "UserCreateInternalData", "UserCreateData", "UserUpdateData", "UserPasswordChangeData",
    "RoleCreateData", "RoleUpdateData", "PermissionData",
    "PurchaseInvoiceLineBaseData", "PurchaseInvoiceBaseData", "PurchaseInvoiceCreateData", "PurchaseInvoiceUpdateData", "PurchaseInvoiceData", "PurchaseInvoiceSummaryData",
    "BankAccountBaseData", "BankAccountCreateData", "BankAccountUpdateData", "BankAccountSummaryData",
    "BankTransactionBaseData", "BankTransactionCreateData", "BankTransactionSummaryData",
    "PaymentAllocationBaseData", "PaymentBaseData", "PaymentCreateData", "PaymentSummaryData",
    "AuditLogEntryData", "DataChangeHistoryEntryData",
    "BankReconciliationBaseData", "BankReconciliationCreateData", "BankReconciliationData",
    "BankReconciliationSummaryData",
    "DashboardKPIData",
    "CSVImportErrorData",
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
class BankTransactionSummaryData(AppBaseModel): 
    id: int
    transaction_date: date
    value_date: Optional[date] = None
    transaction_type: BankTransactionTypeEnum
    description: str
    reference: Optional[str] = None
    amount: Decimal
    is_reconciled: bool = False
    updated_at: datetime

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

# --- CSV Import DTOs ---
class CSVImportErrorData(AppBaseModel):
    row_number: int
    row_data: List[str]
    error_message: str

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
    ar_aging_current: Decimal = Field(Decimal(0)) 
    ar_aging_1_30: Decimal = Field(Decimal(0))
    ar_aging_31_60: Decimal = Field(Decimal(0))
    ar_aging_61_90: Decimal = Field(Decimal(0))
    ar_aging_91_plus: Decimal = Field(Decimal(0))
    ap_aging_current: Decimal = Field(Decimal(0)) 
    ap_aging_1_30: Decimal = Field(Decimal(0))
    ap_aging_31_60: Decimal = Field(Decimal(0))
    ap_aging_61_90: Decimal = Field(Decimal(0))
    ap_aging_91_plus: Decimal = Field(Decimal(0))
    total_current_assets: Decimal = Field(Decimal(0))
    total_current_liabilities: Decimal = Field(Decimal(0))
    total_inventory: Decimal = Field(Decimal(0))
    total_liabilities: Decimal = Field(Decimal(0))
    total_equity: Decimal = Field(Decimal(0))
    current_ratio: Optional[Decimal] = None
    quick_ratio: Optional[Decimal] = None
    debt_to_equity_ratio: Optional[Decimal] = None

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
from datetime import date, datetime, timedelta 
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload, joinedload 
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result
from app.common.enums import JournalTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    # ... (get_by_id, get_all, get_all_summary, get_by_entry_no, get_by_date_range, get_posted_entries_by_date_range - unchanged from previous file set 2)
    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.currency), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension1), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension2), selectinload(JournalEntry.fiscal_period), selectinload(JournalEntry.created_by_user), selectinload(JournalEntry.updated_by_user)).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, start_date_filter: Optional[date] = None, end_date_filter: Optional[date] = None, status_filter: Optional[str] = None, entry_no_filter: Optional[str] = None, description_filter: Optional[str] = None, journal_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        async with self.db_manager.session() as session:
            conditions = []
            if start_date_filter: conditions.append(JournalEntry.entry_date >= start_date_filter)
            if end_date_filter: conditions.append(JournalEntry.entry_date <= end_date_filter)
            if status_filter:
                if status_filter.lower() == "draft": conditions.append(JournalEntry.is_posted == False)
                elif status_filter.lower() == "posted": conditions.append(JournalEntry.is_posted == True)
            if entry_no_filter: conditions.append(JournalEntry.entry_no.ilike(f"%{entry_no_filter}%"))
            if description_filter: conditions.append(JournalEntry.description.ilike(f"%{description_filter}%"))
            if journal_type_filter: conditions.append(JournalEntry.journal_type == journal_type_filter)
            stmt = select(JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted, func.sum(JournalEntryLine.debit_amount).label("total_debits")).join(JournalEntryLine, JournalEntry.id == JournalEntryLine.journal_entry_id, isouter=True)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.group_by(JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            summaries: List[Dict[str, Any]] = []
            for row in result.mappings().all(): summaries.append({"id": row.id, "entry_no": row.entry_no, "date": row.entry_date, "description": row.description, "type": row.journal_type, "total_amount": row.total_debits if row.total_debits is not None else Decimal(0), "status": "Posted" if row.is_posted else "Draft"})
            return summaries
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_no == entry_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj)).where(JournalEntry.is_posted == True, JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt); return list(result.unique().scalars().all())
    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry); await session.flush(); await session.refresh(journal_entry)
            if journal_entry.lines is not None: await session.refresh(journal_entry, attribute_names=['lines'])
            return journal_entry
    async def add(self, entity: JournalEntry) -> JournalEntry: return await self.save(entity)
    async def update(self, entity: JournalEntry) -> JournalEntry: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entry = await session.get(JournalEntry, id_val)
            if entry:
                if entry.is_posted:
                    if self.app_core and hasattr(self.app_core, 'logger'): self.app_core.logger.warning(f"JournalService: Deletion of posted journal entry ID {id_val} prevented.") 
                    return False 
                await session.delete(entry); return True
        return False
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc_stmt = select(Account.opening_balance, Account.opening_balance_date).where(Account.id == account_id)
            acc_res = await session.execute(acc_stmt); acc_data = acc_res.first()
            opening_balance = acc_data.opening_balance if acc_data and acc_data.opening_balance is not None else Decimal(0)
            ob_date = acc_data.opening_balance_date if acc_data and acc_data.opening_balance_date is not None else None
            je_activity_stmt = (select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True, JournalEntry.entry_date <= as_of_date))
            if ob_date: je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            result = await session.execute(je_activity_stmt); je_net_activity = result.scalar_one_or_none() or Decimal(0)
            return opening_balance + je_net_activity
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True, JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date))
            result = await session.execute(stmt); balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: 
        async with self.db_manager.session() as session:
            conditions = [
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ]
            if dimension1_id is not None:
                conditions.append(JournalEntryLine.dimension1_id == dimension1_id)
            if dimension2_id is not None:
                conditions.append(JournalEntryLine.dimension2_id == dimension2_id)

            stmt = select(JournalEntryLine).options(
                joinedload(JournalEntryLine.journal_entry) 
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)\
            .where(and_(*conditions))\
            .order_by(JournalEntry.entry_date, JournalEntry.entry_no, JournalEntryLine.line_number)
            
            result = await session.execute(stmt)
            return list(result.scalars().all()) 

    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).options(joinedload(RecurringPattern.template_journal_entry).selectinload(JournalEntry.lines)).where(RecurringPattern.is_active == True, RecurringPattern.next_generation_date <= as_of_date, or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt); return list(result.scalars().unique().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern); await session.flush(); await session.refresh(pattern)
            return pattern

```

# app/services/audit_services.py
```py
# File: app/services/audit_services.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple, Union # Ensure Union is imported
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, aliased
from datetime import datetime, date # date might not be used directly but good to have with datetime

from app.core.database_manager import DatabaseManager
from app.models.audit.audit_log import AuditLog
from app.models.audit.data_change_history import DataChangeHistory
from app.models.core.user import User 
from app.services import IRepository # Base repository interface
from app.utils.pydantic_models import AuditLogEntryData, DataChangeHistoryEntryData
# from app.utils.result import Result # Not typically returned by services, but managers
from app.common.enums import DataChangeTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    # from sqlalchemy.ext.asyncio import AsyncSession # If session is passed around

# Define Interfaces (can also be in __init__.py, but here for clarity with service)
class IAuditLogRepository(IRepository[AuditLog, int]):
    @abstractmethod
    async def get_audit_logs_paginated(
        self,
        user_id_filter: Optional[int] = None,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: # Returns list of DTOs and total count
        pass

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]):
    @abstractmethod
    async def get_data_change_history_paginated(
        self,
        table_name_filter: Optional[str] = None,
        record_id_filter: Optional[int] = None,
        changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]: # Returns list of DTOs and total count
        pass


class AuditLogService(IAuditLogRepository, IDataChangeHistoryRepository): 
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core # app_core can be used for accessing logger or other global components

    # --- Standard IRepository Stubs (Audit logs are mostly read-only from app perspective) ---
    async def get_by_id(self, id_val: int) -> Optional[Union[AuditLog, DataChangeHistory]]:
        # This method might be less useful for audit logs which are usually queried by context, not ID.
        # However, implementing for interface compliance or specific edge cases.
        async with self.db_manager.session() as session:
            log_entry = await session.get(AuditLog, id_val)
            if log_entry:
                # Could convert to DTO here if consistency is desired, but service usually returns ORM
                return log_entry
            history_entry = await session.get(DataChangeHistory, id_val)
            return history_entry # Could also be DTO
            
    async def get_all(self) -> List[Union[AuditLog, DataChangeHistory]]:
        # Not practical for potentially huge audit tables. Use paginated methods.
        raise NotImplementedError("Use paginated methods for audit logs. Get_all is not supported.")

    async def add(self, entity: Union[AuditLog, DataChangeHistory]) -> Union[AuditLog, DataChangeHistory]:
        # Audit logs are typically generated by database triggers or specialized logging calls, not generic add.
        raise NotImplementedError("Audit logs are system-generated and cannot be added via this service.")

    async def update(self, entity: Union[AuditLog, DataChangeHistory]) -> Union[AuditLog, DataChangeHistory]:
        # Audit logs should be immutable.
        raise NotImplementedError("Audit logs are immutable and cannot be updated.")

    async def delete(self, id_val: int) -> bool:
        # Audit logs should generally not be deleted programmatically, archiving is preferred.
        raise NotImplementedError("Audit logs should not be deleted programmatically via this service.")

    # --- Custom Service Methods for Audit Logs ---

    def _format_changes_summary(self, changes_jsonb: Optional[Dict[str, Any]]) -> Optional[str]:
        if not changes_jsonb:
            return None
        
        summary_parts = []
        old_data = changes_jsonb.get('old')
        new_data = changes_jsonb.get('new')

        action = "Modified" # Default action
        if isinstance(new_data, dict) and old_data is None:
            action = "Created"
        elif new_data is None and isinstance(old_data, dict):
            action = "Deleted"
        
        if action == "Created" and isinstance(new_data, dict):
            # For created records, list some key fields if possible, or just confirm creation
            # Example: List up to 3 non-sensitive fields.
            keys_to_show = [k for k in new_data.keys() if k not in ["id", "created_at", "updated_at", "password_hash", "logo"]][:3]
            if keys_to_show:
                details = ", ".join([f"{k}: '{str(new_data[k])[:30]}...'" if len(str(new_data[k])) > 30 else f"{k}: '{str(new_data[k])}'" for k in keys_to_show])
                summary_parts.append(f"Record {action}. Details: {details}")
            else:
                summary_parts.append(f"Record {action}.")
        elif action == "Deleted" and isinstance(old_data, dict):
            summary_parts.append(f"Record {action}.")
        elif action == "Modified" and isinstance(new_data, dict) and isinstance(old_data, dict):
            changed_fields_count = 0
            for key, new_val in new_data.items():
                if key in ["created_at", "updated_at", "password_hash", "logo"]: # Skip noisy or sensitive fields
                    continue 
                old_val = old_data.get(key) # Use .get() in case old_data doesn't have the key (new field added to schema)
                
                # Handle cases where a value might be a list or dict itself (e.g. JSONB field)
                # For simplicity, we'll compare their string representations for this summary
                str_old_val = str(old_val)
                str_new_val = str(new_val)

                if str_old_val != str_new_val: 
                    changed_fields_count += 1
                    if changed_fields_count <= 3: # Show details for first few changes
                        summary_parts.append(
                            f"'{key}': '{str_old_val[:30]}...' -> '{str_new_val[:30]}...'" 
                            if len(str_old_val) > 30 or len(str_new_val) > 30 
                            else f"'{key}': '{str_old_val}' -> '{str_new_val}'"
                        )
            if changed_fields_count > 3:
                summary_parts.append(f"...and {changed_fields_count - 3} other field(s).")
            if not summary_parts and changed_fields_count == 0 : # Only timestamps / sensitive fields changed
                 summary_parts.append("Minor updates (e.g., timestamps).")

        return "; ".join(summary_parts) if summary_parts else "No changes detailed or only sensitive fields updated."


    async def get_audit_logs_paginated(
        self,
        user_id_filter: Optional[int] = None,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]:
        async with self.db_manager.session() as session:
            conditions = []
            if user_id_filter is not None:
                conditions.append(AuditLog.user_id == user_id_filter)
            if action_filter:
                conditions.append(AuditLog.action.ilike(f"%{action_filter}%")) # Case-insensitive search
            if entity_type_filter:
                conditions.append(AuditLog.entity_type.ilike(f"%{entity_type_filter}%"))
            if entity_id_filter is not None:
                conditions.append(AuditLog.entity_id == entity_id_filter)
            if start_date_filter:
                conditions.append(AuditLog.timestamp >= start_date_filter)
            if end_date_filter: # Add 1 day to end_date_filter to make it inclusive of the whole day
                conditions.append(AuditLog.timestamp < (end_date_filter + datetime.timedelta(days=1)))


            UserAlias = aliased(User, name="user_alias") # Explicit alias name
            
            # Count total matching records
            count_stmt = select(func.count(AuditLog.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            total_count_res = await session.execute(count_stmt)
            total_count = total_count_res.scalar_one()

            # Fetch paginated records
            stmt = select(AuditLog, UserAlias.username.label("username")).outerjoin(
                UserAlias, AuditLog.user_id == UserAlias.id # Ensure correct join condition
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(AuditLog.timestamp.desc()) # type: ignore[attr-defined]
            if page_size > 0: # Allow page_size=0 or negative to fetch all (though not recommended for large tables)
                 stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            log_entries_data: List[AuditLogEntryData] = []
            
            for row_mapping in result.mappings().all(): # Use mappings() for dict-like access
                log_orm = row_mapping[AuditLog]
                username = row_mapping["username"] if row_mapping["username"] else \
                           (f"User ID: {log_orm.user_id}" if log_orm.user_id else "System/Unknown")
                
                log_entries_data.append(AuditLogEntryData(
                    id=log_orm.id,
                    timestamp=log_orm.timestamp,
                    username=username,
                    action=log_orm.action,
                    entity_type=log_orm.entity_type,
                    entity_id=log_orm.entity_id,
                    entity_name=log_orm.entity_name,
                    changes_summary=self._format_changes_summary(log_orm.changes),
                    ip_address=log_orm.ip_address
                ))
            return log_entries_data, total_count

    async def get_data_change_history_paginated(
        self,
        table_name_filter: Optional[str] = None,
        record_id_filter: Optional[int] = None,
        changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]:
        async with self.db_manager.session() as session:
            conditions = []
            if table_name_filter:
                conditions.append(DataChangeHistory.table_name.ilike(f"%{table_name_filter}%"))
            if record_id_filter is not None:
                conditions.append(DataChangeHistory.record_id == record_id_filter)
            if changed_by_user_id_filter is not None:
                conditions.append(DataChangeHistory.changed_by == changed_by_user_id_filter)
            if start_date_filter:
                conditions.append(DataChangeHistory.changed_at >= start_date_filter)
            if end_date_filter: # Add 1 day to end_date_filter to make it inclusive of the whole day
                conditions.append(DataChangeHistory.changed_at < (end_date_filter + datetime.timedelta(days=1)))


            UserAlias = aliased(User, name="changed_by_user_alias") # Explicit alias name

            # Count total matching records
            count_stmt = select(func.count(DataChangeHistory.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            total_count_res = await session.execute(count_stmt)
            total_count = total_count_res.scalar_one()

            # Fetch paginated records
            stmt = select(DataChangeHistory, UserAlias.username.label("changed_by_username")).outerjoin(
                UserAlias, DataChangeHistory.changed_by == UserAlias.id # Ensure correct join condition
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(DataChangeHistory.changed_at.desc()) # type: ignore[attr-defined]
            if page_size > 0:
                 stmt = stmt.limit(page_size).offset((page - 1) * page_size)

            result = await session.execute(stmt)
            history_entries_data: List[DataChangeHistoryEntryData] = []

            for row_mapping in result.mappings().all(): # Use mappings() for dict-like access
                hist_orm = row_mapping[DataChangeHistory]
                username = row_mapping["changed_by_username"] if row_mapping["changed_by_username"] else \
                           (f"User ID: {hist_orm.changed_by}" if hist_orm.changed_by else "System/Unknown")
                
                history_entries_data.append(DataChangeHistoryEntryData(
                    id=hist_orm.id,
                    changed_at=hist_orm.changed_at,
                    table_name=hist_orm.table_name,
                    record_id=hist_orm.record_id,
                    field_name=hist_orm.field_name,
                    old_value=hist_orm.old_value,
                    new_value=hist_orm.new_value,
                    change_type=DataChangeTypeEnum(hist_orm.change_type), # Convert string from DB to Enum
                    changed_by_username=username
                ))
            return history_entries_data, total_count

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
from typing import List, Optional, Any, Generic, TypeVar, Dict, Tuple 
from datetime import date, datetime 
from decimal import Decimal 
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
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
from app.models.business.inventory_movement import InventoryMovement
from app.models.accounting.dimension import Dimension 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction 
from app.models.business.payment import Payment, PaymentAllocation 
from app.models.audit.audit_log import AuditLog 
from app.models.audit.data_change_history import DataChangeHistory 
from app.models.business.bank_reconciliation import BankReconciliation

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData,
    AuditLogEntryData, DataChangeHistoryEntryData, BankReconciliationData,
    BankReconciliationSummaryData, 
    DashboardKPIData
)
from app.utils.result import Result 
from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum, DataChangeTypeEnum 
)

# --- Interfaces ---
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
    @abstractmethod
    async def get_total_balance_by_account_category_and_type_pattern(self, account_category: str, account_type_name_like: str, as_of_date: date) -> Decimal: pass

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
                              description_filter: Optional[str] = None,
                              journal_type_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]: pass
    @abstractmethod
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: pass 

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
    @abstractmethod
    async def get_total_outstanding_balance(self) -> Decimal: pass
    @abstractmethod 
    async def get_total_overdue_balance(self) -> Decimal: pass
    @abstractmethod
    async def get_ar_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass

class IVendorRepository(IRepository[Vendor, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass
    @abstractmethod
    async def get_total_outstanding_balance(self) -> Decimal: pass
    @abstractmethod 
    async def get_total_overdue_balance(self) -> Decimal: pass
    @abstractmethod
    async def get_ap_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass

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
    @abstractmethod 
    async def get_outstanding_invoices_for_customer(self, customer_id: Optional[int], as_of_date: date) -> List[SalesInvoice]: pass


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
    @abstractmethod 
    async def get_outstanding_invoices_for_vendor(self, vendor_id: Optional[int], as_of_date: date) -> List[PurchaseInvoice]: pass


class IInventoryMovementRepository(IRepository[InventoryMovement, int]):
    @abstractmethod
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession]=None) -> InventoryMovement: pass

class IDimensionRepository(IRepository[Dimension, int]):
    @abstractmethod
    async def get_distinct_dimension_types(self) -> List[str]: pass
    @abstractmethod
    async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]: pass
    @abstractmethod
    async def get_by_type_and_code(self, dim_type: str, code: str) -> Optional[Dimension]: pass

class IBankAccountRepository(IRepository[BankAccount, int]):
    @abstractmethod
    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True, 
                              currency_code: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[BankAccountSummaryData]: pass
    @abstractmethod
    async def save(self, entity: BankAccount) -> BankAccount: pass
    @abstractmethod # New method for DashboardManager
    async def get_by_gl_account_id(self, gl_account_id: int) -> Optional[BankAccount]: pass


class IBankTransactionRepository(IRepository[BankTransaction, int]):
    @abstractmethod
    async def get_all_for_bank_account(self, bank_account_id: int,
                                       start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       transaction_type: Optional[BankTransactionTypeEnum] = None,
                                       is_reconciled: Optional[bool] = None,
                                       is_from_statement_filter: Optional[bool] = None, 
                                       page: int = 1, page_size: int = 50
                                      ) -> List[BankTransactionSummaryData]: pass 
    @abstractmethod
    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction: pass

class IPaymentRepository(IRepository[Payment, int]):
    @abstractmethod
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]: pass
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: pass

class IAuditLogRepository(IRepository[AuditLog, int]):
    @abstractmethod
    async def get_audit_logs_paginated(
        self, user_id_filter: Optional[int] = None, action_filter: Optional[str] = None, entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None, start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: pass 

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]):
    @abstractmethod
    async def get_data_change_history_paginated(
        self, table_name_filter: Optional[str] = None, record_id_filter: Optional[int] = None, changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]: pass 

class IBankReconciliationRepository(IRepository[BankReconciliation, int]):
    @abstractmethod
    async def get_or_create_draft_reconciliation(
        self, 
        bank_account_id: int, 
        statement_date: date, 
        statement_ending_balance: Decimal, 
        user_id: int, 
        session: AsyncSession
    ) -> BankReconciliation: pass

    @abstractmethod
    async def mark_transactions_as_provisionally_reconciled(
        self, 
        draft_reconciliation_id: int, 
        transaction_ids: List[int], 
        statement_date: date, 
        user_id: int, 
        session: AsyncSession
    ) -> bool: pass

    @abstractmethod
    async def finalize_reconciliation(
        self, 
        draft_reconciliation_id: int, 
        statement_ending_balance: Decimal, 
        calculated_book_balance: Decimal, 
        reconciled_difference: Decimal,
        user_id: int,
        session: AsyncSession
    ) -> Result[BankReconciliation]: pass 

    @abstractmethod
    async def unreconcile_transactions( 
        self, 
        transaction_ids: List[int], 
        user_id: int, 
        session: AsyncSession
    ) -> bool: pass
    
    @abstractmethod 
    async def get_reconciliations_for_account(
        self, 
        bank_account_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[BankReconciliationSummaryData], int]: pass
    
    @abstractmethod 
    async def get_transactions_for_reconciliation(
        self, 
        reconciliation_id: int
    ) -> Tuple[List[BankTransactionSummaryData], List[BankTransactionSummaryData]]: pass


from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService, DimensionService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
    BankAccountService, BankTransactionService, PaymentService, 
    BankReconciliationService
)
from .audit_services import AuditLogService 

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", "IPurchaseInvoiceRepository", 
    "IInventoryMovementRepository", 
    "IDimensionRepository", 
    "IBankAccountRepository", 
    "IBankTransactionRepository", 
    "IPaymentRepository", 
    "IAuditLogRepository", "IDataChangeHistoryRepository", 
    "IBankReconciliationRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService", "DimensionService", 
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", "PurchaseInvoiceService", 
    "InventoryMovementService", 
    "BankAccountService", 
    "BankTransactionService",
    "PaymentService", 
    "AuditLogService", 
    "BankReconciliationService", 
]

```

# app/services/accounting_services.py
```py
# File: app/services/accounting_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date
from sqlalchemy import select, and_, or_, distinct # Added distinct
from app.models.accounting.account_type import AccountType
from app.models.accounting.currency import Currency
from app.models.accounting.exchange_rate import ExchangeRate
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.dimension import Dimension # New import
from app.core.database_manager import DatabaseManager
from app.services import (
    IAccountTypeRepository, 
    ICurrencyRepository, 
    IExchangeRateRepository,
    IFiscalYearRepository,
    IDimensionRepository # New import
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
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(FiscalYear, id_val)
            if entity:
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
                FiscalYear.start_date <= end_date,
                FiscalYear.end_date >= start_date
            ]
            if exclude_id is not None:
                conditions.append(FiscalYear.id != exclude_id)
            
            stmt = select(FiscalYear).where(and_(*conditions))
            result = await session.execute(stmt)
            return result.scalars().first()

# --- New DimensionService ---
class DimensionService(IDimensionRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[Dimension]:
        async with self.db_manager.session() as session:
            return await session.get(Dimension, id_val)

    async def get_all(self) -> List[Dimension]:
        async with self.db_manager.session() as session:
            stmt = select(Dimension).order_by(Dimension.dimension_type, Dimension.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: Dimension) -> Dimension:
        # User audit fields are on UserAuditMixin, assumed to be set by manager
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Dimension) -> Dimension:
        # User audit fields are on UserAuditMixin, assumed to be set by manager
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        # Add checks if dimension is in use before deleting
        async with self.db_manager.session() as session:
            entity = await session.get(Dimension, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_distinct_dimension_types(self) -> List[str]:
        async with self.db_manager.session() as session:
            stmt = select(distinct(Dimension.dimension_type)).where(Dimension.is_active == True).order_by(Dimension.dimension_type)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]:
        async with self.db_manager.session() as session:
            conditions = [Dimension.dimension_type == dim_type]
            if active_only:
                conditions.append(Dimension.is_active == True)
            stmt = select(Dimension).where(and_(*conditions)).order_by(Dimension.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_type_and_code(self, dim_type: str, code: str) -> Optional[Dimension]:
        async with self.db_manager.session() as session:
            stmt = select(Dimension).where(
                Dimension.dimension_type == dim_type,
                Dimension.code == code,
                Dimension.is_active == True
            )
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
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import select, func, text, and_ 
from app.models.accounting.account import Account 
from app.models.accounting.journal_entry import JournalEntryLine, JournalEntry 
from app.core.database_manager import DatabaseManager
from app.services import IAccountRepository 
from decimal import Decimal
from datetime import date 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.journal_service import JournalService 

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

    async def get_total_balance_by_account_category_and_type_pattern(
        self, 
        account_category: str, 
        account_type_name_like: str, 
        as_of_date: date
    ) -> Decimal:
        total_balance = Decimal(0)
        if not self.app_core:
            if hasattr(self, 'logger') and self.logger:
                 self.logger.error("ApplicationCore not available in AccountService for JournalService access.")
            raise RuntimeError("ApplicationCore context not available in AccountService.")

        journal_service: "JournalService" = self.app_core.journal_service
        if not journal_service:
            if hasattr(self, 'logger') and self.logger:
                 self.logger.error("JournalService not available via ApplicationCore in AccountService.")
            raise RuntimeError("JournalService not available.")

        async with self.db_manager.session() as session:
            stmt = select(Account).where(
                Account.is_active == True,
                Account.account_type == account_category, 
                Account.sub_type.ilike(account_type_name_like) 
            )
            result = await session.execute(stmt)
            accounts_to_sum: List[Account] = list(result.scalars().all())

            for acc in accounts_to_sum:
                balance = await journal_service.get_account_balance(acc.id, as_of_date)
                total_balance += balance
        
        return total_balance.quantize(Decimal("0.01"))

```

# app/services/business_services.py
```py
# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple
from sqlalchemy import select, func, and_, or_, literal_column, case, update as sqlalchemy_update, table, column
from sqlalchemy.types import DECIMAL 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 
from datetime import date, datetime, timedelta 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine 
from app.models.business.inventory_movement import InventoryMovement 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction
from app.models.business.payment import Payment, PaymentAllocation 
from app.models.business.bank_reconciliation import BankReconciliation
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.models.core.user import User
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository, IInventoryMovementRepository,
    IBankAccountRepository, IBankTransactionRepository, IPaymentRepository,
    IBankReconciliationRepository
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData, BankReconciliationSummaryData
)
from app.utils.result import Result 
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

customer_balances_view_table = table(
    "customer_balances",
    column("outstanding_balance", DECIMAL(15, 2)), 
    column("overdue_amount", DECIMAL(15, 2)),
    schema="business"
)

vendor_balances_view_table = table(
    "vendor_balances",
    column("outstanding_balance", DECIMAL(15, 2)),
    column("overdue_amount", DECIMAL(15, 2)),
    schema="business"
)

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
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")
    async def get_total_outstanding_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(customer_balances_view_table.c.outstanding_balance))
            result = await session.execute(stmt)
            total_outstanding = result.scalar_one_or_none()
            return total_outstanding if total_outstanding is not None else Decimal(0)
    async def get_total_overdue_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(customer_balances_view_table.c.overdue_amount))
            result = await session.execute(stmt)
            total_overdue = result.scalar_one_or_none()
            return total_overdue if total_overdue is not None else Decimal(0)
    
    async def get_ar_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]:
        aging_summary = {
            "Current": Decimal(0),    
            "1-30 Days": Decimal(0),  
            "31-60 Days": Decimal(0), 
            "61-90 Days": Decimal(0), 
            "91+ Days": Decimal(0)    
        }
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).where(
                SalesInvoice.status.in_([InvoiceStatusEnum.APPROVED.value, InvoiceStatusEnum.PARTIALLY_PAID.value, InvoiceStatusEnum.OVERDUE.value]),
                SalesInvoice.total_amount > SalesInvoice.amount_paid
            )
            result = await session.execute(stmt)
            outstanding_invoices: List[SalesInvoice] = list(result.scalars().all())

            for inv in outstanding_invoices:
                outstanding_balance = inv.total_amount - inv.amount_paid
                if outstanding_balance <= Decimal("0.005"): 
                    continue
                
                days_overdue = (as_of_date - inv.due_date).days

                if days_overdue <= 0: # Not yet due or due today
                    aging_summary["Current"] += outstanding_balance
                elif 1 <= days_overdue <= 30:
                    aging_summary["1-30 Days"] += outstanding_balance
                elif 31 <= days_overdue <= 60:
                    aging_summary["31-60 Days"] += outstanding_balance
                elif 61 <= days_overdue <= 90:
                    aging_summary["61-90 Days"] += outstanding_balance
                else: # days_overdue >= 91
                    aging_summary["91+ Days"] += outstanding_balance
        
        return {k: v.quantize(Decimal("0.01")) for k, v in aging_summary.items()}


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
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")
    async def get_total_outstanding_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(vendor_balances_view_table.c.outstanding_balance))
            result = await session.execute(stmt)
            total_outstanding = result.scalar_one_or_none()
            return total_outstanding if total_outstanding is not None else Decimal(0)
    async def get_total_overdue_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(vendor_balances_view_table.c.overdue_amount))
            result = await session.execute(stmt)
            total_overdue = result.scalar_one_or_none()
            return total_overdue if total_overdue is not None else Decimal(0)

    async def get_ap_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]:
        aging_summary = {
            "Current": Decimal(0),    
            "1-30 Days": Decimal(0),  
            "31-60 Days": Decimal(0),
            "61-90 Days": Decimal(0),
            "91+ Days": Decimal(0)
        }
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).where(
                PurchaseInvoice.status.in_([InvoiceStatusEnum.APPROVED.value, InvoiceStatusEnum.PARTIALLY_PAID.value, InvoiceStatusEnum.OVERDUE.value]),
                PurchaseInvoice.total_amount > PurchaseInvoice.amount_paid
            )
            result = await session.execute(stmt)
            outstanding_invoices: List[PurchaseInvoice] = list(result.scalars().all())

            for inv in outstanding_invoices:
                outstanding_balance = inv.total_amount - inv.amount_paid
                if outstanding_balance <= Decimal("0.005"):
                    continue
                
                days_overdue = (as_of_date - inv.due_date).days

                if days_overdue <= 0:
                    aging_summary["Current"] += outstanding_balance
                elif 1 <= days_overdue <= 30:
                    aging_summary["1-30 Days"] += outstanding_balance
                elif 31 <= days_overdue <= 60:
                    aging_summary["31-60 Days"] += outstanding_balance
                elif 61 <= days_overdue <= 90:
                    aging_summary["61-90 Days"] += outstanding_balance
                else: 
                    aging_summary["91+ Days"] += outstanding_balance
        
        return {k: v.quantize(Decimal("0.01")) for k, v in aging_summary.items()}

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
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")

class SalesInvoiceService(ISalesInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj),selectinload(SalesInvoice.customer), selectinload(SalesInvoice.currency),selectinload(SalesInvoice.journal_entry), selectinload(SalesInvoice.created_by_user), selectinload(SalesInvoice.updated_by_user)).where(SalesInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if customer_id is not None: conditions.append(SalesInvoice.customer_id == customer_id)
            if status: conditions.append(SalesInvoice.status == status.value)
            if start_date: conditions.append(SalesInvoice.invoice_date >= start_date)
            if end_date: conditions.append(SalesInvoice.invoice_date <= end_date)
            stmt = select( SalesInvoice.id, SalesInvoice.invoice_no, SalesInvoice.invoice_date, SalesInvoice.due_date, Customer.name.label("customer_name"), SalesInvoice.total_amount, SalesInvoice.amount_paid, SalesInvoice.status, SalesInvoice.currency_code).join(Customer, SalesInvoice.customer_id == Customer.id) 
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
            if invoice.id and invoice.lines: await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def update(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        raise NotImplementedError("Hard delete of sales invoices is not supported. Use voiding/cancellation.")
    async def get_outstanding_invoices_for_customer(self, customer_id: Optional[int], as_of_date: date) -> List[SalesInvoice]: # New for aging
        async with self.db_manager.session() as session:
            conditions = [
                SalesInvoice.status.in_([
                    InvoiceStatusEnum.APPROVED.value, 
                    InvoiceStatusEnum.PARTIALLY_PAID.value, 
                    InvoiceStatusEnum.OVERDUE.value
                ]),
                SalesInvoice.total_amount > SalesInvoice.amount_paid,
                SalesInvoice.invoice_date <= as_of_date # Include invoices issued on or before as_of_date
            ]
            if customer_id is not None:
                conditions.append(SalesInvoice.customer_id == customer_id)
            
            stmt = select(SalesInvoice).where(and_(*conditions))
            result = await session.execute(stmt)
            return list(result.scalars().all())

class PurchaseInvoiceService(IPurchaseInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product),selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.tax_code_obj),selectinload(PurchaseInvoice.vendor), selectinload(PurchaseInvoice.currency),selectinload(PurchaseInvoice.journal_entry),selectinload(PurchaseInvoice.created_by_user), selectinload(PurchaseInvoice.updated_by_user)).where(PurchaseInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, vendor_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[PurchaseInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if vendor_id is not None: conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            if status: conditions.append(PurchaseInvoice.status == status.value)
            if start_date: conditions.append(PurchaseInvoice.invoice_date >= start_date)
            if end_date: conditions.append(PurchaseInvoice.invoice_date <= end_date)
            stmt = select( PurchaseInvoice.id, PurchaseInvoice.invoice_no, PurchaseInvoice.vendor_invoice_no, PurchaseInvoice.invoice_date, Vendor.name.label("vendor_name"), PurchaseInvoice.total_amount, PurchaseInvoice.status, PurchaseInvoice.currency_code).join(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [PurchaseInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.invoice_no == internal_ref_no) 
            result = await session.execute(stmt); return result.scalars().first()
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.vendor_id == vendor_id, PurchaseInvoice.vendor_invoice_no == vendor_invoice_no)
            result = await session.execute(stmt); return result.scalars().first() 
    async def save(self, invoice: PurchaseInvoice) -> PurchaseInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def update(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        async with self.db_manager.session() as session:
            pi = await session.get(PurchaseInvoice, invoice_id)
            if pi and pi.status == InvoiceStatusEnum.DRAFT.value: await session.delete(pi); return True
            elif pi: self.logger.warning(f"Attempt to delete non-draft PI ID {invoice_id} with status {pi.status}. Denied."); raise ValueError(f"Cannot delete PI {pi.invoice_no} as its status is '{pi.status}'. Only Draft invoices can be deleted.")
        return False
    async def get_outstanding_invoices_for_vendor(self, vendor_id: Optional[int], as_of_date: date) -> List[PurchaseInvoice]: # New for aging
        async with self.db_manager.session() as session:
            conditions = [
                PurchaseInvoice.status.in_([
                    InvoiceStatusEnum.APPROVED.value, 
                    InvoiceStatusEnum.PARTIALLY_PAID.value, 
                    InvoiceStatusEnum.OVERDUE.value
                ]),
                PurchaseInvoice.total_amount > PurchaseInvoice.amount_paid,
                PurchaseInvoice.invoice_date <= as_of_date
            ]
            if vendor_id is not None:
                conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            
            stmt = select(PurchaseInvoice).where(and_(*conditions))
            result = await session.execute(stmt)
            return list(result.scalars().all())

class InventoryMovementService(IInventoryMovementRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[InventoryMovement]:
        async with self.db_manager.session() as session: return await session.get(InventoryMovement, id_val)
    async def get_all(self) -> List[InventoryMovement]:
        async with self.db_manager.session() as session:
            stmt = select(InventoryMovement).order_by(InventoryMovement.movement_date.desc(), InventoryMovement.id.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession] = None) -> InventoryMovement:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity); return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: InventoryMovement) -> InventoryMovement: return await self.save(entity) 
    async def update(self, entity: InventoryMovement) -> InventoryMovement:
        self.logger.warning(f"Update called on InventoryMovementService for ID {entity.id}. Typically movements are immutable.")
        return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        self.logger.warning(f"Hard delete attempted for InventoryMovement ID {id_val}. This is generally not recommended.")
        async with self.db_manager.session() as session:
            entity = await session.get(InventoryMovement, id_val)
            if entity: await session.delete(entity); return True
            return False

class BankAccountService(IBankAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).options(selectinload(BankAccount.currency),selectinload(BankAccount.gl_account),selectinload(BankAccount.created_by_user),selectinload(BankAccount.updated_by_user)).where(BankAccount.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).order_by(BankAccount.account_name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True, currency_code: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[BankAccountSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only: conditions.append(BankAccount.is_active == True)
            if currency_code: conditions.append(BankAccount.currency_code == currency_code)
            stmt = select(BankAccount.id, BankAccount.account_name, BankAccount.bank_name,BankAccount.account_number, BankAccount.currency_code,BankAccount.current_balance, BankAccount.is_active,Account.code.label("gl_account_code"), Account.name.label("gl_account_name")).join(Account, BankAccount.gl_account_id == Account.id)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(BankAccount.account_name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [BankAccountSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]
    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).where(BankAccount.account_number == account_number); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, entity: BankAccount) -> BankAccount:
        async with self.db_manager.session() as session:
            session.add(entity); await session.flush(); await session.refresh(entity); return entity
    async def add(self, entity: BankAccount) -> BankAccount: return await self.save(entity)
    async def update(self, entity: BankAccount) -> BankAccount: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        bank_account = await self.get_by_id(id_val)
        if bank_account:
            if bank_account.is_active: bank_account.is_active = False; await self.save(bank_account); return True
            else: self.logger.info(f"BankAccount ID {id_val} is already inactive. No change made by delete."); return True 
        return False
    async def get_by_gl_account_id(self, gl_account_id: int) -> Optional[BankAccount]: # New method
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).where(BankAccount.gl_account_id == gl_account_id)
            result = await session.execute(stmt)
            return result.scalars().first()

class BankTransactionService(IBankTransactionRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[BankTransaction]:
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).options(selectinload(BankTransaction.bank_account),selectinload(BankTransaction.journal_entry), selectinload(BankTransaction.created_by_user),selectinload(BankTransaction.updated_by_user)).where(BankTransaction.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[BankTransaction]: 
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).order_by(BankTransaction.transaction_date.desc(), BankTransaction.id.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_for_bank_account(self, bank_account_id: int,start_date: Optional[date] = None,end_date: Optional[date] = None,transaction_type: Optional[BankTransactionTypeEnum] = None,is_reconciled: Optional[bool] = None,is_from_statement_filter: Optional[bool] = None, page: int = 1, page_size: int = 50) -> List[BankTransactionSummaryData]:
        async with self.db_manager.session() as session:
            conditions = [BankTransaction.bank_account_id == bank_account_id]
            if start_date: conditions.append(BankTransaction.transaction_date >= start_date)
            if end_date: conditions.append(BankTransaction.transaction_date <= end_date)
            if transaction_type: conditions.append(BankTransaction.transaction_type == transaction_type.value)
            if is_reconciled is not None: conditions.append(BankTransaction.is_reconciled == is_reconciled)
            if is_from_statement_filter is not None: conditions.append(BankTransaction.is_from_statement == is_from_statement_filter)
            stmt = select(BankTransaction).where(and_(*conditions)).order_by(BankTransaction.transaction_date.desc(), BankTransaction.value_date.desc(), BankTransaction.id.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); txns_orm = result.scalars().all()
            summaries: List[BankTransactionSummaryData] = []
            for txn in txns_orm:
                summaries.append(BankTransactionSummaryData(id=txn.id,transaction_date=txn.transaction_date,value_date=txn.value_date,transaction_type=BankTransactionTypeEnum(txn.transaction_type), description=txn.description,reference=txn.reference,amount=txn.amount, is_reconciled=txn.is_reconciled, updated_at=txn.updated_at))
            return summaries
    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity); return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: BankTransaction) -> BankTransaction: return await self.save(entity)
    async def update(self, entity: BankTransaction) -> BankTransaction: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(BankTransaction, id_val)
            if entity:
                if entity.is_reconciled: self.logger.warning(f"Attempt to delete reconciled BankTransaction ID {id_val}. Denied."); return False 
                await session.delete(entity); return True
            return False

class PaymentService(IPaymentRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(selectinload(Payment.allocations),selectinload(Payment.bank_account),selectinload(Payment.currency),selectinload(Payment.journal_entry),selectinload(Payment.created_by_user),selectinload(Payment.updated_by_user)).where(Payment.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(selectinload(Payment.allocations)).where(Payment.payment_no == payment_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all_summary(self, entity_type: Optional[PaymentEntityTypeEnum] = None,entity_id: Optional[int] = None,status: Optional[PaymentStatusEnum] = None,start_date: Optional[date] = None,end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[PaymentSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if entity_type: conditions.append(Payment.entity_type == entity_type.value)
            if entity_id is not None: conditions.append(Payment.entity_id == entity_id)
            if status: conditions.append(Payment.status == status.value)
            if start_date: conditions.append(Payment.payment_date >= start_date)
            if end_date: conditions.append(Payment.payment_date <= end_date)
            stmt = select(Payment.id, Payment.payment_no, Payment.payment_date, Payment.payment_type,Payment.payment_method, Payment.entity_type, Payment.entity_id,Payment.amount, Payment.currency_code, Payment.status,case((Payment.entity_type == PaymentEntityTypeEnum.CUSTOMER.value, select(Customer.name).where(Customer.id == Payment.entity_id).scalar_subquery()),(Payment.entity_type == PaymentEntityTypeEnum.VENDOR.value, select(Vendor.name).where(Vendor.id == Payment.entity_id).scalar_subquery()),else_=literal_column("'Other/N/A'")).label("entity_name"))
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [PaymentSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity)
            if entity.id and entity.allocations: await current_session.refresh(entity, attribute_names=['allocations'])
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: Payment) -> Payment: return await self.save(entity)
    async def update(self, entity: Payment) -> Payment: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            payment = await session.get(Payment, id_val)
            if payment:
                if payment.status == PaymentStatusEnum.DRAFT.value: await session.delete(payment); self.logger.info(f"Draft Payment ID {id_val} deleted."); return True
                else: self.logger.warning(f"Attempt to delete non-draft Payment ID {id_val} (status: {payment.status}). Denied."); return False 
            return False

class BankReconciliationService(IBankReconciliationRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[BankReconciliation]:
        async with self.db_manager.session() as session:
            stmt = select(BankReconciliation).options(
                selectinload(BankReconciliation.created_by_user) 
            ).where(BankReconciliation.id == id_val)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[BankReconciliation]:
        async with self.db_manager.session() as session:
            stmt = select(BankReconciliation).order_by(BankReconciliation.statement_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        return await self.save(entity, session)

    async def update(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        return await self.save(entity, session)

    async def delete(self, id_val: int) -> bool:
        self.logger.warning(f"Deletion of BankReconciliation ID {id_val} attempted. This operation un-reconciles linked transactions.")
        async with self.db_manager.session() as session: 
            async with session.begin(): 
                update_stmt = (
                    sqlalchemy_update(BankTransaction)
                    .where(BankTransaction.reconciled_bank_reconciliation_id == id_val)
                    .values(is_reconciled=False, reconciled_date=None, reconciled_bank_reconciliation_id=None)
                    .execution_options(synchronize_session=False) 
                )
                await session.execute(update_stmt)
                entity = await session.get(BankReconciliation, id_val)
                if entity:
                    await session.delete(entity)
                    return True
            return False 
            
    async def save(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity)
            await current_session.flush()
            await current_session.refresh(entity)
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: # type: ignore
                return await _save_logic(new_session)

    async def get_or_create_draft_reconciliation(
        self, 
        bank_account_id: int, 
        statement_date: date, 
        statement_ending_balance: Decimal, 
        user_id: int, 
        session: AsyncSession
    ) -> BankReconciliation:
        draft_stmt = select(BankReconciliation).where(
            BankReconciliation.bank_account_id == bank_account_id,
            BankReconciliation.statement_date == statement_date,
            BankReconciliation.status == "Draft"
        )
        result = await session.execute(draft_stmt)
        existing_draft = result.scalars().first()

        if existing_draft:
            self.logger.info(f"Found existing draft reconciliation ID {existing_draft.id} for account {bank_account_id} on {statement_date}.")
            if existing_draft.statement_ending_balance != statement_ending_balance:
                existing_draft.statement_ending_balance = statement_ending_balance
            return existing_draft
        else:
            self.logger.info(f"Creating new draft reconciliation for account {bank_account_id} on {statement_date}.")
            new_draft = BankReconciliation(
                bank_account_id=bank_account_id,
                statement_date=statement_date,
                statement_ending_balance=statement_ending_balance,
                calculated_book_balance=Decimal(0), 
                reconciled_difference=statement_ending_balance, 
                status="Draft",
                created_by_user_id=user_id
            )
            session.add(new_draft)
            await session.flush()
            await session.refresh(new_draft)
            return new_draft

    async def mark_transactions_as_provisionally_reconciled(
        self, 
        draft_reconciliation_id: int, 
        transaction_ids: List[int], 
        statement_date: date, 
        user_id: int, 
        session: AsyncSession
    ) -> bool:
        if not transaction_ids:
            return True 

        update_stmt = (
            sqlalchemy_update(BankTransaction)
            .where(BankTransaction.id.in_(transaction_ids))
            .values(
                is_reconciled=True,
                reconciled_date=statement_date,
                reconciled_bank_reconciliation_id=draft_reconciliation_id
            )
            .execution_options(synchronize_session=False) 
        )
        result = await session.execute(update_stmt)
        self.logger.info(f"Marked {result.rowcount} transactions as provisionally reconciled for draft recon ID {draft_reconciliation_id}.")
        return result.rowcount == len(transaction_ids)


    async def finalize_reconciliation(
        self, 
        draft_reconciliation_id: int, 
        statement_ending_balance: Decimal, 
        calculated_book_balance: Decimal, 
        reconciled_difference: Decimal,
        user_id: int,
        session: AsyncSession 
    ) -> Result[BankReconciliation]:
        recon_orm = await session.get(BankReconciliation, draft_reconciliation_id, options=[selectinload(BankReconciliation.bank_account)])
        if not recon_orm:
            return Result.failure([f"Draft Reconciliation ID {draft_reconciliation_id} not found."])
        if recon_orm.status == "Finalized":
            return Result.failure([f"Reconciliation ID {draft_reconciliation_id} is already finalized."])

        recon_orm.status = "Finalized"
        recon_orm.statement_ending_balance = statement_ending_balance
        recon_orm.calculated_book_balance = calculated_book_balance
        recon_orm.reconciled_difference = reconciled_difference
        recon_orm.reconciliation_date = datetime.now(datetime.timezone.utc) 
        
        if recon_orm.bank_account:
            recon_orm.bank_account.last_reconciled_date = recon_orm.statement_date
            recon_orm.bank_account.last_reconciled_balance = recon_orm.statement_ending_balance 
            session.add(recon_orm.bank_account)
        else:
            self.logger.error(f"BankAccount not found for Reconciliation ID {draft_reconciliation_id} during finalization.")
            return Result.failure([f"Associated BankAccount for Reconciliation ID {draft_reconciliation_id} not found."])
            
        session.add(recon_orm)
        return Result.success(recon_orm)

    async def unreconcile_transactions( 
        self, 
        transaction_ids: List[int], 
        user_id: int, 
        session: AsyncSession
    ) -> bool:
        if not transaction_ids:
            return True
        
        update_stmt = (
            sqlalchemy_update(BankTransaction)
            .where(BankTransaction.id.in_(transaction_ids))
            .values(
                is_reconciled=False,
                reconciled_date=None,
                reconciled_bank_reconciliation_id=None
            )
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(update_stmt)
        self.logger.info(f"Unreconciled {result.rowcount} transactions.")
        return result.rowcount == len(transaction_ids)

    async def get_reconciliations_for_account(
        self, 
        bank_account_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[BankReconciliationSummaryData], int]:
        async with self.db_manager.session() as session:
            base_conditions = [
                BankReconciliation.bank_account_id == bank_account_id,
                BankReconciliation.status == "Finalized" 
            ]
            
            count_stmt = select(func.count(BankReconciliation.id)).where(and_(*base_conditions))
            total_count_res = await session.execute(count_stmt)
            total_records = total_count_res.scalar_one_or_none() or 0

            stmt = select(BankReconciliation, User.username.label("created_by_username"))\
                .join(User, BankReconciliation.created_by_user_id == User.id)\
                .where(and_(*base_conditions))\
                .order_by(BankReconciliation.statement_date.desc(), BankReconciliation.id.desc()) 
            
            if page_size > 0:
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            summaries: List[BankReconciliationSummaryData] = []
            for row in result.mappings().all():
                recon_orm = row[BankReconciliation]
                summaries.append(BankReconciliationSummaryData(
                    id=recon_orm.id, statement_date=recon_orm.statement_date,
                    statement_ending_balance=recon_orm.statement_ending_balance,
                    reconciled_difference=recon_orm.reconciled_difference,
                    reconciliation_date=recon_orm.reconciliation_date,
                    created_by_username=row.created_by_username
                ))
            return summaries, total_records

    async def get_transactions_for_reconciliation(
        self, reconciliation_id: int
    ) -> Tuple[List[BankTransactionSummaryData], List[BankTransactionSummaryData]]:
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction)\
                .where(BankTransaction.reconciled_bank_reconciliation_id == reconciliation_id)\
                .order_by(BankTransaction.updated_at.desc(), BankTransaction.id) 
            
            result = await session.execute(stmt)
            all_txns_orm = result.scalars().all()

            statement_items: List[BankTransactionSummaryData] = []
            system_items: List[BankTransactionSummaryData] = []

            for txn_orm in all_txns_orm:
                summary_dto = BankTransactionSummaryData(
                    id=txn_orm.id, transaction_date=txn_orm.transaction_date,
                    value_date=txn_orm.value_date, transaction_type=BankTransactionTypeEnum(txn_orm.transaction_type),
                    description=txn_orm.description, reference=txn_orm.reference,
                    amount=txn_orm.amount, is_reconciled=txn_orm.is_reconciled, 
                    updated_at=txn_orm.updated_at
                )
                if txn_orm.is_from_statement:
                    statement_items.append(summary_dto)
                else:
                    system_items.append(summary_dto)
            
            return statement_items, system_items

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

# app/core/config_manager.py
```py
# File: app/core/config_manager.py
# (Content as previously generated and verified)
import os
import sys 
import configparser
from types import SimpleNamespace
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file_name: str = "config.ini", app_name: str = "SGBookkeeper"):
        if os.name == 'nt': 
            self.config_dir = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming')) / app_name
        elif sys.platform == 'darwin': 
            self.config_dir = Path.home() / 'Library' / 'Application Support' / app_name
        else: 
            self.config_dir = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config')) / app_name
        
        self.config_file_path = self.config_dir / config_file_name
        os.makedirs(self.config_dir, exist_ok=True)

        self.parser = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        if not self.config_file_path.exists():
            self._create_default_config()
        self.parser.read(self.config_file_path)

    def _create_default_config(self):
        self.parser['Database'] = {
            'username': 'postgres',
            'password': '', 
            'host': 'localhost',
            'port': '5432',
            'database': 'sg_bookkeeper',
            'echo_sql': 'False',
            'pool_min_size': '2',
            'pool_max_size': '10',
            'pool_recycle_seconds': '3600'
        }
        self.parser['Application'] = {
            'theme': 'light',
            'language': 'en',
            'last_opened_company_id': '' 
        }
        with open(self.config_file_path, 'w') as f:
            self.parser.write(f)

    def get_database_config(self):
        db_config = self.parser['Database']
        return SimpleNamespace(
            username=db_config.get('username', 'postgres'),
            password=db_config.get('password', ''), 
            host=db_config.get('host', 'localhost'),
            port=db_config.getint('port', 5432),
            database=db_config.get('database', 'sg_bookkeeper'),
            echo_sql=db_config.getboolean('echo_sql', False),
            pool_min_size=db_config.getint('pool_min_size', 2),
            pool_max_size=db_config.getint('pool_max_size', 10),
            pool_recycle_seconds=db_config.getint('pool_recycle_seconds', 3600)
        )

    def get_app_config(self):
        app_config = self.parser['Application']
        return SimpleNamespace(
            theme=app_config.get('theme', 'light'),
            language=app_config.get('language', 'en'),
            last_opened_company_id=app_config.get('last_opened_company_id', '')
        )

    def get_setting(self, section: str, key: str, fallback=None):
        try:
            return self.parser.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback


    def set_setting(self, section: str, key: str, value: str):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))
        with open(self.config_file_path, 'w') as f:
            self.parser.write(f)

```

# app/core/security_manager.py
```py
# File: app/core/security_manager.py
import bcrypt
from typing import Optional, List, cast
from app.models.core.user import User, Role, Permission 
from app.models.accounting.account import Account 
from sqlalchemy import select, update, delete, func # Added func
from sqlalchemy.orm import selectinload, joinedload
from app.core.database_manager import DatabaseManager 
import datetime 
from app.utils.result import Result
from app.utils.pydantic_models import (
    UserSummaryData, UserCreateInternalData, UserRoleAssignmentData,
    UserCreateData, UserUpdateData, UserPasswordChangeData,
    RoleCreateData, RoleUpdateData, PermissionData 
)


class SecurityManager:
    def __init__(self, db_manager: DatabaseManager): 
        self.db_manager = db_manager
        self.current_user: Optional[User] = None

    # ... (hash_password, verify_password, authenticate_user, logout_user, get_current_user, has_permission - unchanged) ...
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8') 

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError: 
            return False

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        async with self.db_manager.session() as session:
            stmt = select(User).options(
                selectinload(User.roles).selectinload(Role.permissions) 
            ).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if user and user.is_active:
                if self.verify_password(password, user.password_hash):
                    self.current_user = user
                    user.last_login = datetime.datetime.now(datetime.timezone.utc) 
                    user.failed_login_attempts = 0
                    await session.commit() 
                    return user
                else: 
                    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                    user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
                    if user.failed_login_attempts >= 5: 
                        user.is_active = False 
                        if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                             self.db_manager.logger.warning(f"User account '{username}' locked due to too many failed login attempts.")
                    await session.commit() 
            elif user and not user.is_active:
                if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                    self.db_manager.logger.warning(f"Login attempt for inactive user account '{username}'.")
                user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc) 
                await session.commit()
        self.current_user = None 
        return None

    def logout_user(self):
        self.current_user = None

    def get_current_user(self) -> Optional[User]:
        return self.current_user

    def has_permission(self, required_permission_code: str) -> bool: 
        if not self.current_user or not self.current_user.is_active:
            return False
        if any(role.name == 'Administrator' for role in self.current_user.roles):
            return True 
        if not self.current_user.roles:
             return False 
        for role in self.current_user.roles:
            if not role.permissions: continue
            for perm in role.permissions:
                if perm.code == required_permission_code:
                    return True
        return False
    
    async def create_user_from_internal_data(self, user_data: UserCreateInternalData) -> Result[User]:
        async with self.db_manager.session() as session:
            stmt_exist = select(User).where(User.username == user_data.username)
            if (await session.execute(stmt_exist)).scalars().first():
                return Result.failure([f"Username '{user_data.username}' already exists."])
            if user_data.email:
                stmt_email_exist = select(User).where(User.email == str(user_data.email)) 
                if (await session.execute(stmt_email_exist)).scalars().first():
                    return Result.failure([f"Email '{user_data.email}' already registered."])

            new_user = User(
                username=user_data.username, password_hash=user_data.password_hash, 
                email=str(user_data.email) if user_data.email else None, 
                full_name=user_data.full_name, is_active=user_data.is_active,
            )
            
            if user_data.assigned_roles:
                role_ids = [r.role_id for r in user_data.assigned_roles]
                if role_ids: 
                    roles_q = await session.execute(select(Role).where(Role.id.in_(role_ids))) # type: ignore
                    db_roles = roles_q.scalars().all()
                    if len(db_roles) != len(set(role_ids)): 
                        found_role_ids = {r.id for r in db_roles}
                        missing_roles = [r_id for r_id in role_ids if r_id not in found_role_ids]
                        if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                            self.db_manager.logger.warning(f"During user creation, roles with IDs not found: {missing_roles}")
                    new_user.roles.extend(db_roles) 
            
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            if new_user.roles: 
                 await session.refresh(new_user, attribute_names=['roles'])
            return Result.success(new_user)

    async def create_user_with_roles(self, dto: UserCreateData) -> Result[User]:
        hashed_password = self.hash_password(dto.password)
        
        role_assignments: List[UserRoleAssignmentData] = []
        if dto.assigned_role_ids:
            role_assignments = [UserRoleAssignmentData(role_id=r_id) for r_id in dto.assigned_role_ids]

        internal_dto = UserCreateInternalData(
            username=dto.username,
            full_name=dto.full_name,
            email=dto.email,
            is_active=dto.is_active,
            password_hash=hashed_password,
            assigned_roles=role_assignments
        )
        return await self.create_user_from_internal_data(internal_dto)
            
    async def get_all_users_summary(self) -> List[UserSummaryData]:
        async with self.db_manager.session() as session:
            stmt = select(User).options(selectinload(User.roles)).order_by(User.username)
            result = await session.execute(stmt)
            users_orm = result.scalars().unique().all()
            
            summaries: List[UserSummaryData] = []
            for user in users_orm:
                summaries.append(UserSummaryData(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                    email=user.email, 
                    is_active=user.is_active,
                    last_login=user.last_login,
                    roles=[role.name for role in user.roles if role.name] 
                ))
            return summaries

    async def get_user_by_id_for_edit(self, user_id: int) -> Optional[User]:
        async with self.db_manager.session() as session:
            stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update_user_from_dto(self, dto: UserUpdateData) -> Result[User]:
        async with self.db_manager.session() as session:
            user_to_update = await session.get(User, dto.id, options=[selectinload(User.roles)])
            if not user_to_update:
                return Result.failure([f"User with ID {dto.id} not found."])

            if dto.username != user_to_update.username: 
                stmt_exist = select(User).where(User.username == dto.username, User.id != dto.id)
                if (await session.execute(stmt_exist)).scalars().first():
                    return Result.failure([f"Username '{dto.username}' already exists for another user."])
            
            if dto.email and dto.email != user_to_update.email: 
                stmt_email_exist = select(User).where(User.email == str(dto.email), User.id != dto.id) 
                if (await session.execute(stmt_email_exist)).scalars().first():
                    return Result.failure([f"Email '{dto.email}' already registered by another user."])

            user_to_update.username = dto.username
            user_to_update.full_name = dto.full_name
            user_to_update.email = str(dto.email) if dto.email else None
            user_to_update.is_active = dto.is_active
            user_to_update.updated_at = datetime.datetime.now(datetime.timezone.utc) 

            if dto.assigned_role_ids is not None: 
                new_roles_orm: List[Role] = []
                if dto.assigned_role_ids:
                    roles_q = await session.execute(select(Role).where(Role.id.in_(dto.assigned_role_ids))) # type: ignore
                    new_roles_orm = list(roles_q.scalars().all())
                
                user_to_update.roles.clear() 
                for role_orm in new_roles_orm: 
                    user_to_update.roles.append(role_orm)

            await session.flush()
            await session.refresh(user_to_update)
            await session.refresh(user_to_update, attribute_names=['roles'])
            return Result.success(user_to_update)


    async def toggle_user_active_status(self, user_id_to_toggle: int, current_admin_user_id: int) -> Result[User]:
        if user_id_to_toggle == current_admin_user_id:
            return Result.failure(["Cannot change the active status of your own account."])

        async with self.db_manager.session() as session:
            user = await session.get(User, user_id_to_toggle, options=[selectinload(User.roles)]) 
            if not user:
                return Result.failure([f"User with ID {user_id_to_toggle} not found."])
            
            if user.username == "system_init_user": 
                 return Result.failure(["The 'system_init_user' status cannot be changed."])

            if user.is_active: 
                is_admin = any(role.name == "Administrator" for role in user.roles)
                if is_admin:
                    active_admins_count_stmt = select(func.count(User.id)).join(User.roles).where( # type: ignore
                        Role.name == "Administrator", User.is_active == True
                    )
                    active_admins_count = (await session.execute(active_admins_count_stmt)).scalar_one()
                    if active_admins_count <= 1:
                        return Result.failure(["Cannot deactivate the last active administrator."])
            
            user.is_active = not user.is_active
            user.updated_at = datetime.datetime.now(datetime.timezone.utc)
            
            await session.flush()
            await session.refresh(user)
            return Result.success(user)

    async def get_all_roles(self) -> List[Role]:
        async with self.db_manager.session() as session:
            stmt = select(Role).options(selectinload(Role.permissions)).order_by(Role.name) 
            result = await session.execute(stmt)
            return list(result.scalars().unique().all()) 

    async def change_user_password(self, password_dto: UserPasswordChangeData) -> Result[None]:
        async with self.db_manager.session() as session:
            user = await session.get(User, password_dto.user_id_to_change)
            if not user:
                return Result.failure([f"User with ID {password_dto.user_id_to_change} not found."])
            
            if user.username == "system_init_user":
                 return Result.failure(["Password for 'system_init_user' cannot be changed."])

            user.password_hash = self.hash_password(password_dto.new_password)
            user.require_password_change = False 
            user.updated_at = datetime.datetime.now(datetime.timezone.utc)
            
            await session.flush()
            return Result.success(None)

    # --- Role Management Methods ---
    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        async with self.db_manager.session() as session:
            stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def create_role(self, dto: RoleCreateData, current_admin_user_id: int) -> Result[Role]:
        async with self.db_manager.session() as session:
            stmt_exist = select(Role).where(Role.name == dto.name)
            if (await session.execute(stmt_exist)).scalars().first():
                return Result.failure([f"Role name '{dto.name}' already exists."])
            
            new_role = Role(name=dto.name, description=dto.description)
            # TimestampMixin handles created_at, updated_at
            
            # Assign permissions if provided
            if dto.permission_ids:
                permissions_to_assign: List[Permission] = []
                if dto.permission_ids: # Ensure list is not empty before querying
                    perm_q = await session.execute(select(Permission).where(Permission.id.in_(dto.permission_ids))) # type: ignore
                    permissions_to_assign = list(perm_q.scalars().all())
                    if len(permissions_to_assign) != len(set(dto.permission_ids)):
                        return Result.failure(["One or more provided permission IDs are invalid."])
                new_role.permissions.extend(permissions_to_assign)

            session.add(new_role)
            await session.flush()
            await session.refresh(new_role)
            if new_role.permissions: # Eager load permissions if they were assigned
                await session.refresh(new_role, attribute_names=['permissions'])
            return Result.success(new_role)

    async def update_role(self, dto: RoleUpdateData, current_admin_user_id: int) -> Result[Role]:
        async with self.db_manager.session() as session:
            role_to_update = await session.get(Role, dto.id, options=[selectinload(Role.permissions)])
            if not role_to_update:
                return Result.failure([f"Role with ID {dto.id} not found."])

            if role_to_update.name == "Administrator" and dto.name != "Administrator":
                return Result.failure(["The 'Administrator' role name cannot be changed."])

            if dto.name != role_to_update.name:
                stmt_exist = select(Role).where(Role.name == dto.name, Role.id != dto.id)
                if (await session.execute(stmt_exist)).scalars().first():
                    return Result.failure([f"Role name '{dto.name}' already exists for another role."])
            
            role_to_update.name = dto.name
            role_to_update.description = dto.description
            role_to_update.updated_at = datetime.datetime.now(datetime.timezone.utc)
            
            # Update permissions
            if dto.permission_ids is not None: # Allow passing empty list to clear permissions
                role_to_update.permissions.clear() # Clear existing
                if dto.permission_ids: # If new list is not empty, fetch and assign
                    new_permissions_orm: List[Permission] = []
                    perm_q = await session.execute(select(Permission).where(Permission.id.in_(dto.permission_ids))) # type: ignore
                    new_permissions_orm = list(perm_q.scalars().all())
                    if len(new_permissions_orm) != len(set(dto.permission_ids)):
                        return Result.failure(["One or more selected permission IDs for update are invalid."])
                    for perm in new_permissions_orm:
                        role_to_update.permissions.append(perm)
            
            await session.flush()
            await session.refresh(role_to_update)
            # Ensure permissions are loaded after update
            await session.refresh(role_to_update, attribute_names=['permissions'])
            return Result.success(role_to_update)

    async def delete_role(self, role_id: int, current_admin_user_id: int) -> Result[None]:
        async with self.db_manager.session() as session:
            role_to_delete = await session.get(Role, role_id, options=[selectinload(Role.users)])
            if not role_to_delete:
                return Result.failure([f"Role with ID {role_id} not found."])

            if role_to_delete.name == "Administrator":
                return Result.failure(["The 'Administrator' role cannot be deleted."])
            
            if role_to_delete.users: 
                user_list = ", ".join([user.username for user in role_to_delete.users[:3]]) # Show first 3
                if len(role_to_delete.users) > 3: user_list += "..."
                return Result.failure([f"Role '{role_to_delete.name}' is assigned to users (e.g., {user_list}) and cannot be deleted. Please reassign users first."])
            
            await session.delete(role_to_delete)
            await session.flush() 
            return Result.success(None)

    async def get_all_permissions(self) -> List[PermissionData]:
        async with self.db_manager.session() as session:
            stmt = select(Permission).order_by(Permission.module, Permission.code)
            result = await session.execute(stmt)
            permissions_orm = result.scalars().all()
            return [PermissionData.model_validate(p) for p in permissions_orm]
            
    async def assign_permissions_to_role(self, role_id: int, permission_ids: List[int], current_admin_user_id: int) -> Result[Role]:
        # This method is now effectively covered by update_role if RoleUpdateData contains permission_ids
        # For clarity, it could be kept as a separate endpoint/manager method if preferred,
        # but it would largely duplicate logic from update_role's permission handling.
        # For now, assume update_role is the primary way to modify role details including permissions.
        # If a dedicated "Assign Permissions" UI action is needed, this can call update_role
        # with only the permission_ids changing in the DTO.
        role_orm = await self.get_role_by_id(role_id)
        if not role_orm:
            return Result.failure([f"Role ID {role_id} not found."])
        
        update_dto = RoleUpdateData(
            id=role_id,
            name=role_orm.name, # Keep existing name
            description=role_orm.description, # Keep existing description
            permission_ids=permission_ids # Set new permissions
        )
        return await self.update_role(update_dto, current_admin_user_id)

```

# app/core/__init__.py
```py
# File: app/core/__init__.py
# (Content as previously generated, verified)
from .application_core import ApplicationCore
from .config_manager import ConfigManager
from .database_manager import DatabaseManager
from .module_manager import ModuleManager
from .security_manager import SecurityManager

__all__ = [
    "ApplicationCore",
    "ConfigManager",
    "DatabaseManager",
    "ModuleManager",
    "SecurityManager",
]

```

# app/core/database_manager.py
```py
# File: app/core/database_manager.py
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, TYPE_CHECKING, Any 
import logging # Import standard logging

import asyncpg 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text 

from app.core.config_manager import ConfigManager

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class DatabaseManager:
    def __init__(self, config_manager: ConfigManager, app_core: Optional["ApplicationCore"] = None):
        self.config = config_manager.get_database_config()
        self.app_core = app_core 
        self.engine: Optional[Any] = None 
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self.pool: Optional[asyncpg.Pool] = None
        self.logger: Optional[logging.Logger] = None # Initialize logger attribute

    async def initialize(self):
        if self.engine: 
            return
        
        # Set up logger if not already done by app_core injecting it
        if self.app_core and hasattr(self.app_core, 'logger'):
            self.logger = self.app_core.logger
        elif not self.logger: # Basic fallback logger if app_core didn't set one
            self.logger = logging.getLogger("DatabaseManager")
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)


        connection_string = (
            f"postgresql+asyncpg://{self.config.username}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
        )
        
        self.engine = create_async_engine(
            connection_string,
            echo=self.config.echo_sql,
            pool_size=self.config.pool_min_size,
            max_overflow=self.config.pool_max_size - self.config.pool_min_size,
            pool_recycle=self.config.pool_recycle_seconds
        )
        
        self.session_factory = async_sessionmaker(
            self.engine, 
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        await self._create_pool()
    
    async def _create_pool(self):
        try:
            self.pool = await asyncpg.create_pool(
                user=self.config.username,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size
            )
        except Exception as e:
            if self.logger: self.logger.error(f"Failed to create asyncpg pool: {e}", exc_info=True)
            else: print(f"Failed to create asyncpg pool: {e}")
            self.pool = None 

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]: 
        if not self.session_factory:
            # This log might happen before logger is fully set if initialize isn't called first.
            log_msg = "DatabaseManager not initialized. Call initialize() first."
            if self.logger: self.logger.error(log_msg)
            else: print(f"ERROR: {log_msg}")
            raise RuntimeError(log_msg)
            
        session: AsyncSession = self.session_factory()
        try:
            if self.app_core and self.app_core.current_user:
                user_id_str = str(self.app_core.current_user.id)
                await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id_str}';"))
            # If no app_core.current_user, we DO NOT set app.current_user_id.
            # The audit trigger's fallback logic (EXCEPTION WHEN OTHERS -> v_user_id := NULL; IF v_user_id IS NULL THEN NEW.id for users table)
            # will handle attributing self-updates to core.users or logging NULL for other system actions.
            
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]: 
        if not self.pool:
            if not self.engine: 
                 raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            await self._create_pool() 
            if not self.pool: 
                raise RuntimeError("Failed to acquire asyncpg pool.")
            
        async with self.pool.acquire() as connection:
            if self.app_core and self.app_core.current_user:
                user_id_str = str(self.app_core.current_user.id)
                await connection.execute(f"SET LOCAL app.current_user_id = '{user_id_str}';") # type: ignore
            # Again, do not set if no current_user, let trigger handle it.
            yield connection # type: ignore 
    
    async def execute_query(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, callback): 
        async with self.connection() as conn:
            async with conn.transaction(): # type: ignore 
                return await callback(conn)
    
    async def close_connections(self):
        if self.pool:
            await self.pool.close()
            self.pool = None 
        
        if self.engine:
            await self.engine.dispose() # type: ignore
            self.engine = None

```

# app/core/module_manager.py
```py
# File: app/core/module_manager.py
# (Content as previously generated, verified)
from typing import Dict, Any
# from app.core.application_core import ApplicationCore # Forward declaration

class ModuleManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.modules: Dict[str, Any] = {}
        
    def load_module(self, module_name: str, module_class: type, *args, **kwargs):
        if module_name not in self.modules:
            self.modules[module_name] = module_class(self.app_core, *args, **kwargs)
        return self.modules[module_name]

    def get_module(self, module_name: str) -> Any:
        module_instance = self.modules.get(module_name)
        if not module_instance:
            print(f"Warning: Module '{module_name}' accessed before loading or not registered.")
        return module_instance

    def load_all_modules(self):
        print("ModuleManager: load_all_modules called (conceptual).")

```

# app/core/application_core.py
```py
# File: app/core/application_core.py
from typing import Optional, Any, TYPE_CHECKING
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager 
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

# Manager imports are generally okay here if they don't cause cycles themselves
# (which we are fixing by making managers use TYPE_CHECKING for services)
from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.business_logic.customer_manager import CustomerManager 
from app.business_logic.vendor_manager import VendorManager 
from app.business_logic.product_manager import ProductManager
from app.business_logic.bank_account_manager import BankAccountManager 
from app.business_logic.bank_transaction_manager import BankTransactionManager

# REMOVE All direct service imports from here. They will be imported locally in startup().
# Example of removed lines:
# from app.services.account_service import AccountService
# from app.services.fiscal_period_service import FiscalPeriodService
# etc.

import logging 

if TYPE_CHECKING:
    # Imports for type hinting that might cause circular dependencies if imported at top level
    from app.services.journal_service import JournalService
    from app.accounting.journal_entry_manager import JournalEntryManager
    from app.accounting.fiscal_period_manager import FiscalPeriodManager
    from app.accounting.currency_manager import CurrencyManager
    from app.business_logic.sales_invoice_manager import SalesInvoiceManager
    from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager
    from app.business_logic.payment_manager import PaymentManager
    from app.tax.gst_manager import GSTManager
    from app.tax.tax_calculator import TaxCalculator
    from app.reporting.financial_statement_generator import FinancialStatementGenerator
    from app.reporting.report_engine import ReportEngine
    from app.reporting.dashboard_manager import DashboardManager
    from app.utils.sequence_generator import SequenceGenerator
    
    # Add ALL service classes here for property type hints
    from app.services.account_service import AccountService
    from app.services.fiscal_period_service import FiscalPeriodService
    from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
    from app.services.tax_service import TaxCodeService, GSTReturnService 
    from app.services.accounting_services import (
        AccountTypeService, CurrencyService as CurrencyRepoService, 
        ExchangeRateService, FiscalYearService, DimensionService 
    )
    from app.services.business_services import (
        CustomerService, VendorService, ProductService, 
        SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
        BankAccountService, BankTransactionService, PaymentService, 
        BankReconciliationService
    )
    from app.services.audit_services import AuditLogService

class ApplicationCore:
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.db_manager.app_core = self 
        
        self.logger = logging.getLogger("SGBookkeeperAppCore")
        if not self.logger.handlers:
            handler = logging.StreamHandler(); formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter); self.logger.addHandler(handler); self.logger.setLevel(logging.INFO) 
        if not hasattr(self.db_manager, 'logger') or self.db_manager.logger is None: self.db_manager.logger = self.logger

        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        # Service Instance Placeholders
        self._account_service_instance: Optional["AccountService"] = None
        self._journal_service_instance: Optional["JournalService"] = None 
        self._fiscal_period_service_instance: Optional["FiscalPeriodService"] = None
        self._fiscal_year_service_instance: Optional["FiscalYearService"] = None
        self._sequence_service_instance: Optional["SequenceService"] = None
        self._company_settings_service_instance: Optional["CompanySettingsService"] = None
        self._configuration_service_instance: Optional["ConfigurationService"] = None
        self._tax_code_service_instance: Optional["TaxCodeService"] = None
        self._gst_return_service_instance: Optional["GSTReturnService"] = None
        self._account_type_service_instance: Optional["AccountTypeService"] = None
        self._currency_repo_service_instance: Optional["CurrencyRepoService"] = None
        self._exchange_rate_service_instance: Optional["ExchangeRateService"] = None
        self._dimension_service_instance: Optional["DimensionService"] = None
        self._customer_service_instance: Optional["CustomerService"] = None
        self._vendor_service_instance: Optional["VendorService"] = None
        self._product_service_instance: Optional["ProductService"] = None
        self._sales_invoice_service_instance: Optional["SalesInvoiceService"] = None
        self._purchase_invoice_service_instance: Optional["PurchaseInvoiceService"] = None 
        self._inventory_movement_service_instance: Optional["InventoryMovementService"] = None
        self._bank_account_service_instance: Optional["BankAccountService"] = None 
        self._bank_transaction_service_instance: Optional["BankTransactionService"] = None
        self._payment_service_instance: Optional["PaymentService"] = None
        self._audit_log_service_instance: Optional["AuditLogService"] = None
        self._bank_reconciliation_service_instance: Optional["BankReconciliationService"] = None

        # Manager Instance Placeholders
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional["JournalEntryManager"] = None 
        self._fp_manager_instance: Optional["FiscalPeriodManager"] = None
        self._currency_manager_instance: Optional["CurrencyManager"] = None
        self._gst_manager_instance: Optional["GSTManager"] = None
        self._tax_calculator_instance: Optional["TaxCalculator"] = None
        self._financial_statement_generator_instance: Optional["FinancialStatementGenerator"] = None
        self._report_engine_instance: Optional["ReportEngine"] = None
        self._customer_manager_instance: Optional[CustomerManager] = None
        self._vendor_manager_instance: Optional[VendorManager] = None
        self._product_manager_instance: Optional[ProductManager] = None
        self._sales_invoice_manager_instance: Optional["SalesInvoiceManager"] = None
        self._purchase_invoice_manager_instance: Optional["PurchaseInvoiceManager"] = None
        self._bank_account_manager_instance: Optional[BankAccountManager] = None
        self._bank_transaction_manager_instance: Optional[BankTransactionManager] = None
        self._payment_manager_instance: Optional["PaymentManager"] = None
        self._dashboard_manager_instance: Optional["DashboardManager"] = None
        
        self.logger.info("ApplicationCore initialized.")

    async def startup(self):
        self.logger.info("ApplicationCore starting up...")
        await self.db_manager.initialize() 
        
        # Import services locally within startup
        from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
        from app.services.account_service import AccountService
        from app.services.fiscal_period_service import FiscalPeriodService
        from app.services.accounting_services import (
            AccountTypeService, CurrencyService as CurrencyRepoService, 
            ExchangeRateService, FiscalYearService, DimensionService 
        )
        from app.services.tax_service import TaxCodeService, GSTReturnService 
        from app.services.business_services import (
            CustomerService, VendorService, ProductService, 
            SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
            BankAccountService, BankTransactionService, PaymentService, 
            BankReconciliationService
        )
        from app.services.audit_services import AuditLogService
        from app.services.journal_service import JournalService 
        
        # Initialize services
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager)
        self._account_service_instance = AccountService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager) # FiscalPeriodService does not take app_core
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self)
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)
        self._dimension_service_instance = DimensionService(self.db_manager, self)
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        self._customer_service_instance = CustomerService(self.db_manager, self)
        self._vendor_service_instance = VendorService(self.db_manager, self) 
        self._product_service_instance = ProductService(self.db_manager, self)
        self._sales_invoice_service_instance = SalesInvoiceService(self.db_manager, self)
        self._purchase_invoice_service_instance = PurchaseInvoiceService(self.db_manager, self) 
        self._inventory_movement_service_instance = InventoryMovementService(self.db_manager, self) 
        self._bank_account_service_instance = BankAccountService(self.db_manager, self) 
        self._bank_transaction_service_instance = BankTransactionService(self.db_manager, self)
        self._payment_service_instance = PaymentService(self.db_manager, self) 
        self._audit_log_service_instance = AuditLogService(self.db_manager, self)
        self._bank_reconciliation_service_instance = BankReconciliationService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        
        from app.utils.sequence_generator import SequenceGenerator 
        py_sequence_generator = SequenceGenerator(self.sequence_service, app_core_ref=self) 
        
        from app.accounting.journal_entry_manager import JournalEntryManager
        from app.accounting.fiscal_period_manager import FiscalPeriodManager
        from app.accounting.currency_manager import CurrencyManager
        from app.tax.gst_manager import GSTManager
        from app.tax.tax_calculator import TaxCalculator
        from app.reporting.financial_statement_generator import FinancialStatementGenerator
        from app.reporting.report_engine import ReportEngine
        from app.reporting.dashboard_manager import DashboardManager
        from app.business_logic.sales_invoice_manager import SalesInvoiceManager
        from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager
        from app.business_logic.payment_manager import PaymentManager
        
        # Initialize Managers
        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        self._je_manager_instance = JournalEntryManager(self.journal_service, self.account_service, self.fiscal_period_service, self)
        self._fp_manager_instance = FiscalPeriodManager(self) 
        self._currency_manager_instance = CurrencyManager(self) 
        self._tax_calculator_instance = TaxCalculator(self.tax_code_service) 
        self._gst_manager_instance = GSTManager(self.tax_code_service, self.journal_service, self.company_settings_service, self.gst_return_service, self.account_service, self.fiscal_period_service, py_sequence_generator, self)
        self._financial_statement_generator_instance = FinancialStatementGenerator(self.account_service, self.journal_service, self.fiscal_period_service, self.account_type_service, self.tax_code_service, self.company_settings_service, self.dimension_service)
        self._report_engine_instance = ReportEngine(self)
        self._customer_manager_instance = CustomerManager(customer_service=self.customer_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._vendor_manager_instance = VendorManager( vendor_service=self.vendor_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._product_manager_instance = ProductManager( product_service=self.product_service, account_service=self.account_service, tax_code_service=self.tax_code_service, app_core=self)
        self._sales_invoice_manager_instance = SalesInvoiceManager(sales_invoice_service=self.sales_invoice_service, customer_service=self.customer_service, product_service=self.product_service, tax_code_service=self.tax_code_service, tax_calculator=self.tax_calculator, sequence_service=self.sequence_service, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self, inventory_movement_service=self.inventory_movement_service)
        self._purchase_invoice_manager_instance = PurchaseInvoiceManager( purchase_invoice_service=self.purchase_invoice_service, vendor_service=self.vendor_service, product_service=self.product_service, tax_code_service=self.tax_code_service, tax_calculator=self.tax_calculator, sequence_service=self.sequence_service, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self, inventory_movement_service=self.inventory_movement_service)
        self._bank_account_manager_instance = BankAccountManager( bank_account_service=self.bank_account_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._bank_transaction_manager_instance = BankTransactionManager( bank_transaction_service=self.bank_transaction_service, bank_account_service=self.bank_account_service, app_core=self)
        self._payment_manager_instance = PaymentManager( payment_service=self.payment_service, sequence_service=self.sequence_service, bank_account_service=self.bank_account_service, customer_service=self.customer_service, vendor_service=self.vendor_service, sales_invoice_service=self.sales_invoice_service, purchase_invoice_service=self.purchase_invoice_service, journal_entry_manager=self.journal_entry_manager, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self)
        self._dashboard_manager_instance = DashboardManager(self)
        
        self.module_manager.load_all_modules() 
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self): 
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    # Service Properties
    @property
    def account_service(self) -> "AccountService": 
        if not self._account_service_instance: raise RuntimeError("AccountService not initialized.")
        return self._account_service_instance
    @property
    def journal_service(self) -> "JournalService": 
        if not self._journal_service_instance: raise RuntimeError("JournalService not initialized.")
        return self._journal_service_instance 
    @property
    def fiscal_period_service(self) -> "FiscalPeriodService": 
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    @property
    def fiscal_year_service(self) -> "FiscalYearService": 
        if not self._fiscal_year_service_instance: raise RuntimeError("FiscalYearService not initialized.")
        return self._fiscal_year_service_instance
    @property
    def sequence_service(self) -> "SequenceService": 
        if not self._sequence_service_instance: raise RuntimeError("SequenceService not initialized.")
        return self._sequence_service_instance
    @property
    def company_settings_service(self) -> "CompanySettingsService": 
        if not self._company_settings_service_instance: raise RuntimeError("CompanySettingsService not initialized.")
        return self._company_settings_service_instance
    @property
    def configuration_service(self) -> "ConfigurationService": 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance
    @property
    def tax_code_service(self) -> "TaxCodeService": 
        if not self._tax_code_service_instance: raise RuntimeError("TaxCodeService not initialized.")
        return self._tax_code_service_instance
    @property
    def gst_return_service(self) -> "GSTReturnService": 
        if not self._gst_return_service_instance: raise RuntimeError("GSTReturnService not initialized.")
        return self._gst_return_service_instance
    @property
    def account_type_service(self) -> "AccountTypeService":  
        if not self._account_type_service_instance: raise RuntimeError("AccountTypeService not initialized.")
        return self._account_type_service_instance 
    @property
    def currency_repo_service(self) -> "CurrencyRepoService": 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property 
    def currency_service(self) -> "CurrencyRepoService": 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyService (CurrencyRepoService) not initialized.")
        return self._currency_repo_service_instance
    @property
    def exchange_rate_service(self) -> "ExchangeRateService": 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def dimension_service(self) -> "DimensionService": 
        if not self._dimension_service_instance: raise RuntimeError("DimensionService not initialized.")
        return self._dimension_service_instance
    @property
    def customer_service(self) -> "CustomerService": 
        if not self._customer_service_instance: raise RuntimeError("CustomerService not initialized.")
        return self._customer_service_instance
    @property
    def vendor_service(self) -> "VendorService": 
        if not self._vendor_service_instance: raise RuntimeError("VendorService not initialized.")
        return self._vendor_service_instance
    @property
    def product_service(self) -> "ProductService": 
        if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
        return self._product_service_instance
    @property
    def sales_invoice_service(self) -> "SalesInvoiceService": 
        if not self._sales_invoice_service_instance: raise RuntimeError("SalesInvoiceService not initialized.")
        return self._sales_invoice_service_instance
    @property
    def purchase_invoice_service(self) -> "PurchaseInvoiceService": 
        if not self._purchase_invoice_service_instance: raise RuntimeError("PurchaseInvoiceService not initialized.")
        return self._purchase_invoice_service_instance
    @property
    def inventory_movement_service(self) -> "InventoryMovementService": 
        if not self._inventory_movement_service_instance: raise RuntimeError("InventoryMovementService not initialized.")
        return self._inventory_movement_service_instance
    @property
    def bank_account_service(self) -> "BankAccountService": 
        if not self._bank_account_service_instance: raise RuntimeError("BankAccountService not initialized.")
        return self._bank_account_service_instance
    @property
    def bank_transaction_service(self) -> "BankTransactionService": 
        if not self._bank_transaction_service_instance: raise RuntimeError("BankTransactionService not initialized.")
        return self._bank_transaction_service_instance
    @property
    def payment_service(self) -> "PaymentService": 
        if not self._payment_service_instance: raise RuntimeError("PaymentService not initialized.")
        return self._payment_service_instance
    @property
    def audit_log_service(self) -> "AuditLogService": 
        if not self._audit_log_service_instance: raise RuntimeError("AuditLogService not initialized.")
        return self._audit_log_service_instance
    @property
    def bank_reconciliation_service(self) -> "BankReconciliationService":
        if not self._bank_reconciliation_service_instance: raise RuntimeError("BankReconciliationService not initialized.")
        return self._bank_reconciliation_service_instance

    # Manager Properties
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager: 
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property 
    def accounting_service(self) -> ChartOfAccountsManager: 
        return self.chart_of_accounts_manager
    @property
    def journal_entry_manager(self) -> "JournalEntryManager": 
        if not self._je_manager_instance: raise RuntimeError("JournalEntryManager not initialized.")
        return self._je_manager_instance 
    @property
    def fiscal_period_manager(self) -> "FiscalPeriodManager": 
        if not self._fp_manager_instance: raise RuntimeError("FiscalPeriodManager not initialized.")
        return self._fp_manager_instance 
    @property
    def currency_manager(self) -> "CurrencyManager": 
        if not self._currency_manager_instance: raise RuntimeError("CurrencyManager not initialized.")
        return self._currency_manager_instance 
    @property
    def gst_manager(self) -> "GSTManager": 
        if not self._gst_manager_instance: raise RuntimeError("GSTManager not initialized.")
        return self._gst_manager_instance 
    @property
    def tax_calculator(self) -> "TaxCalculator": 
        if not self._tax_calculator_instance: raise RuntimeError("TaxCalculator not initialized.")
        return self._tax_calculator_instance 
    @property
    def financial_statement_generator(self) -> "FinancialStatementGenerator": 
        if not self._financial_statement_generator_instance: raise RuntimeError("FinancialStatementGenerator not initialized.")
        return self._financial_statement_generator_instance 
    @property
    def report_engine(self) -> "ReportEngine": 
        if not self._report_engine_instance: raise RuntimeError("ReportEngine not initialized.")
        return self._report_engine_instance 
    @property
    def customer_manager(self) -> CustomerManager: 
        if not self._customer_manager_instance: raise RuntimeError("CustomerManager not initialized.")
        return self._customer_manager_instance
    @property
    def vendor_manager(self) -> VendorManager: 
        if not self._vendor_manager_instance: raise RuntimeError("VendorManager not initialized.")
        return self._vendor_manager_instance
    @property
    def product_manager(self) -> ProductManager: 
        if not self._product_manager_instance: raise RuntimeError("ProductManager not initialized.")
        return self._product_manager_instance
    @property
    def sales_invoice_manager(self) -> "SalesInvoiceManager": 
        if not self._sales_invoice_manager_instance: raise RuntimeError("SalesInvoiceManager not initialized.")
        return self._sales_invoice_manager_instance 
    @property
    def purchase_invoice_manager(self) -> "PurchaseInvoiceManager": 
        if not self._purchase_invoice_manager_instance: raise RuntimeError("PurchaseInvoiceManager not initialized.")
        return self._purchase_invoice_manager_instance 
    @property
    def bank_account_manager(self) -> BankAccountManager: 
        if not self._bank_account_manager_instance: raise RuntimeError("BankAccountManager not initialized.")
        return self._bank_account_manager_instance
    @property
    def bank_transaction_manager(self) -> BankTransactionManager: 
        if not self._bank_transaction_manager_instance: raise RuntimeError("BankTransactionManager not initialized.")
        return self._bank_transaction_manager_instance
    @property
    def payment_manager(self) -> "PaymentManager": 
        if not self._payment_manager_instance: raise RuntimeError("PaymentManager not initialized.")
        return self._payment_manager_instance 
    @property
    def dashboard_manager(self) -> "DashboardManager":
        if not self._dashboard_manager_instance: raise RuntimeError("DashboardManager not initialized.")
        return self._dashboard_manager_instance 

```

