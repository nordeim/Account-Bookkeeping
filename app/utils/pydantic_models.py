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
            # datetime and date are handled by json_converter/json_date_hook for direct json.dumps/loads
            # but Pydantic v2 handles them correctly by default for model_dump(mode='json')
        }
        validate_assignment = True # Useful for mutable models

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
        if not lines: return values # Already caught by check_lines_not_empty if it's an issue
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
        errors = []
        if not account_data.code: errors.append("Account code is required.")
        if not account_data.name: errors.append("Account name is required.")
        if not account_data.account_type: errors.append("Account type is required.")
        if account_data.is_bank_account and account_data.account_type != 'Asset':
            errors.append("Bank accounts must be of type 'Asset'.")
        if account_data.opening_balance_date and account_data.opening_balance == Decimal(0):
             errors.append("Opening balance date provided but opening balance is zero.")
        if account_data.opening_balance != Decimal(0) and not account_data.opening_balance_date:
             errors.append("Opening balance provided but opening balance date is missing.")
        return errors
    def validate_create(self, account_data: AccountCreateData) -> AccountValidationResult:
        errors = self.validate_common(account_data); return AccountValidationResult(is_valid=not errors, errors=errors)
    def validate_update(self, account_data: AccountUpdateData) -> AccountValidationResult:
        errors = self.validate_common(account_data)
        if not account_data.id: errors.append("Account ID is required for updates.")
        return AccountValidationResult(is_valid=not errors, errors=errors)

# --- Company Setting DTO (existing) ---
class CompanySettingData(AppBaseModel, UserAuditData): # (existing fields)
    id: Optional[int] = None; company_name: str = Field(..., max_length=100)
    legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20)
    gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False
    address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50)
    country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None # Use EmailStr
    website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None 
    fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31)
    base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50)
    date_format: str = Field("dd/MM/yyyy", max_length=20) # Changed default to dd/MM/yyyy

# --- Fiscal Year Related DTOs (existing) ---
class FiscalYearCreateData(AppBaseModel, UserAuditData): # (existing fields)
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date
    auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start, end = values.get('start_date'), values.get('end_date')
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): # (existing fields)
    id: int; name: str; start_date: date; end_date: date
    period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): # (existing fields)
    id: int; year_name: str; start_date: date; end_date: date
    is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = []

# --- NEW: Customer Related DTOs ---
class CustomerBaseData(AppBaseModel):
    customer_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    legal_name: Optional[str] = Field(None, max_length=200)
    uen_no: Optional[str] = Field(None, max_length=20) # Add UEN validator if needed
    gst_registered: bool = False
    gst_no: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None # Pydantic handles email validation
    phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=50)
    country: str = Field("Singapore", max_length=50)
    credit_terms: int = Field(30, ge=0) # Days
    credit_limit: Optional[Decimal] = Field(None, ge=Decimal(0))
    currency_code: str = Field("SGD", min_length=3, max_length=3)
    is_active: bool = True
    customer_since: Optional[date] = None
    notes: Optional[str] = None
    receivables_account_id: Optional[int] = None # Must be an existing 'Asset' type account, ideally AR control

    @validator('credit_limit', pre=True, always=True)
    def credit_limit_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else None
    
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'):
            raise ValueError("GST No. is required if customer is GST registered.")
        return values

class CustomerCreateData(CustomerBaseData, UserAuditData):
    pass

class CustomerUpdateData(CustomerBaseData, UserAuditData):
    id: int

class CustomerData(CustomerBaseData): # For displaying full customer details
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    updated_by_user_id: int
    
class CustomerSummaryData(AppBaseModel): # For table listings
    id: int
    customer_code: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool
    # Add other summary fields if needed, e.g., outstanding_balance (calculated field)

