# File: app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator # type: ignore
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
    def opening_balance_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

class AccountCreateData(AccountBaseData, UserAuditData):
    pass

class AccountUpdateData(AccountBaseData, UserAuditData):
    id: int
    pass

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
        if not lines: 
            return values
        total_debits = sum(line.debit_amount for line in lines)
        total_credits = sum(line.credit_amount for line in lines)
        if abs(total_debits - total_credits) > Decimal("0.01"): 
            raise ValueError(f"Journal entry must be balanced (Debits: {total_debits}, Credits: {total_credits}).")
        return values

# --- GST Return Related DTOs ---
class GSTReturnData(AppBaseModel, UserAuditData):
    id: Optional[int] = None 
    return_period: str = Field(..., max_length=20)
    start_date: date
    end_date: date
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

    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 
               'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 
               'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs ---
class TaxCalculationResultData(AppBaseModel):
    tax_amount: Decimal
    tax_account_id: Optional[int] = None
    taxable_amount: Decimal

class TransactionLineTaxData(AppBaseModel):
    amount: Decimal 
    tax_code: Optional[str] = None
    account_id: Optional[int] = None 
    index: int 

class TransactionTaxData(AppBaseModel):
    transaction_type: str 
    lines: List[TransactionLineTaxData]

# --- Validation Result DTO ---
class AccountValidationResult(AppBaseModel):
    is_valid: bool
    errors: List[str] = []

class AccountValidator:
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
        errors = self.validate_common(account_data)
        return AccountValidationResult(is_valid=not errors, errors=errors)

    def validate_update(self, account_data: AccountUpdateData) -> AccountValidationResult:
        errors = self.validate_common(account_data)
        if not account_data.id: errors.append("Account ID is required for updates.")
        return AccountValidationResult(is_valid=not errors, errors=errors)

class CompanySettingData(AppBaseModel, UserAuditData):
    id: Optional[int] = None 
    company_name: str = Field(..., max_length=100)
    legal_name: Optional[str] = Field(None, max_length=200)
    uen_no: Optional[str] = Field(None, max_length=20)
    gst_registration_no: Optional[str] = Field(None, max_length=20)
    gst_registered: bool = False
    address_line1: Optional[str] = Field(None, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    city: str = Field("Singapore", max_length=50)
    country: str = Field("Singapore", max_length=50)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=100)
    logo: Optional[bytes] = None 
    fiscal_year_start_month: int = Field(1, ge=1, le=12)
    fiscal_year_start_day: int = Field(1, ge=1, le=31)
    base_currency: str = Field("SGD", max_length=3)
    tax_id_label: str = Field("UEN", max_length=50)
    date_format: str = Field("yyyy-MM-dd", max_length=20)

# --- Fiscal Year Related DTOs ---
class FiscalYearCreateData(AppBaseModel, UserAuditData):
    year_name: str = Field(..., max_length=20)
    start_date: date
    end_date: date
    auto_generate_periods: Optional[str] = None # "Monthly", "Quarterly", or None/""

    @root_validator(skip_on_failure=True)
    def check_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start = values.get('start_date')
        end = values.get('end_date')
        if start and end and start >= end:
            raise ValueError("End date must be after start date.")
        # Additional validation: e.g., year should not overlap with existing ones (manager-level)
        return values

class FiscalPeriodData(AppBaseModel): # For listing or returning period info
    id: int
    name: str
    start_date: date
    end_date: date
    period_type: str
    status: str
    period_number: int
    is_adjustment: bool

class FiscalYearData(AppBaseModel): # For listing or returning fiscal year info
    id: int
    year_name: str
    start_date: date
    end_date: date
    is_closed: bool
    closed_date: Optional[datetime] = None
    periods: List[FiscalPeriodData] = []

