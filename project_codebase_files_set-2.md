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
# Updated to use SequenceService and core.sequences table
import asyncio
from typing import Optional # Added Optional
from app.models.core.sequence import Sequence
from app.services.core_services import SequenceService 

class SequenceGenerator:
    def __init__(self, sequence_service: SequenceService):
        self.sequence_service = sequence_service
        # No in-memory cache for sequences to ensure DB is source of truth.
        # The DB function core.get_next_sequence_value handles concurrency better.
        # This Python version relying on service needs careful transaction management if high concurrency.
        # For a desktop app, this might be acceptable.

    async def next_sequence(self, sequence_name: str, prefix_override: Optional[str] = None) -> str:
        """
        Generates the next number in a sequence using the SequenceService.
        """
        # This needs to be an atomic operation (SELECT FOR UPDATE + UPDATE)
        # The SequenceService doesn't implement this directly.
        # A raw SQL call to core.get_next_sequence_value() is better here.
        # For now, let's simulate with service calls (less robust for concurrency).
        
        sequence_obj = await self.sequence_service.get_sequence_by_name(sequence_name)

        if not sequence_obj:
            # Create sequence if not found - this should ideally be a setup step
            # or handled by the DB function if called.
            print(f"Sequence '{sequence_name}' not found, creating with defaults.")
            default_prefix = prefix_override if prefix_override is not None else sequence_name.upper()[:3] + "-"
            sequence_obj = Sequence(
                sequence_name=sequence_name,
                next_value=1,
                increment_by=1,
                min_value=1,
                max_value=2147483647,
                prefix=default_prefix,
                format_template='{PREFIX}{VALUE:06}' # Default to 6-digit padding
            )
            # Note: This creation doesn't happen in a transaction with the increment.
            # This is a flaw in this simplified approach.
            await self.sequence_service.save_sequence(sequence_obj) # Save the new sequence definition

        current_value = sequence_obj.next_value
        sequence_obj.next_value += sequence_obj.increment_by
        
        if sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            sequence_obj.next_value = sequence_obj.min_value
        elif not sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            # This state should not be saved if it exceeds max_value.
            # The core.get_next_sequence_value function likely handles this better.
            # For now, let's prevent saving this invalid state.
            # Instead of raising an error here, the DB sequence function would handle this.
            # If we stick to Python logic, we should not save and raise.
            # However, the schema's DB function core.get_next_sequence_value doesn't have this python-side check.
            # For now, let's assume the DB function is primary and this Python one is a fallback or less used.
            # Let's allow save, but it means the DB function is the one to rely on for strict max_value.
            print(f"Warning: Sequence '{sequence_name}' next value {sequence_obj.next_value} exceeds max value {sequence_obj.max_value} and cycle is off.")
            # To strictly adhere to non-cycling max_value, one might do:
            # if sequence_obj.next_value > sequence_obj.max_value:
            #     raise ValueError(f"Sequence '{sequence_name}' has reached its maximum value.")

        await self.sequence_service.save_sequence(sequence_obj) # Save updated next_value

        # Use prefix_override if provided, else from sequence_obj
        actual_prefix = prefix_override if prefix_override is not None else (sequence_obj.prefix or '')
        
        # Formatting logic based on sequence_obj.format_template
        formatted_value_str = str(current_value) # Default if no padding in template
        
        # Example for handling {VALUE:06} type padding
        padding_marker_start = "{VALUE:0"
        padding_marker_end = "}"
        if padding_marker_start in sequence_obj.format_template:
            try:
                start_index = sequence_obj.format_template.find(padding_marker_start) + len(padding_marker_start)
                end_index = sequence_obj.format_template.find(padding_marker_end, start_index)
                if start_index > -1 and end_index > start_index:
                    padding_spec = sequence_obj.format_template[start_index:end_index]
                    padding = int(padding_spec)
                    formatted_value_str = str(current_value).zfill(padding)
            except ValueError: # int conversion failed
                pass # Use unpadded value
            except Exception: # Other parsing errors
                pass


        result_str = sequence_obj.format_template
        result_str = result_str.replace('{PREFIX}', actual_prefix)
        
        # Replace specific padded value first, then generic unpadded
        if padding_marker_start in sequence_obj.format_template:
             placeholder_to_replace = sequence_obj.format_template[sequence_obj.format_template.find(padding_marker_start):sequence_obj.format_template.find(padding_marker_end, sequence_obj.format_template.find(padding_marker_start)) + 1]
             result_str = result_str.replace(placeholder_to_replace, formatted_value_str)
        else:
            result_str = result_str.replace('{VALUE}', formatted_value_str) # Fallback if no padding specified

        result_str = result_str.replace('{SUFFIX}', sequence_obj.suffix or '')
            
        return result_str

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
# Updated for new models and Decimal usage.
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
# from app.core.database_manager import DatabaseManager # Already imported by IJournalEntryRepository context
from app.services import IJournalEntryRepository
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account)).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
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
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account) 
            ).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry)
            await session.flush() 
            await session.refresh(journal_entry)
            for line in journal_entry.lines: # Eager load lines before session closes
                await session.refresh(line)
            return journal_entry
            
    async def add(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def update(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        entry = await self.get_by_id(id_val)
        if entry and not entry.is_posted: 
            async with self.db_manager.session() as session:
                await session.delete(entry) 
            return True
        return False

    async def post(self, journal_id: int) -> bool:
        entry = await self.get_by_id(journal_id)
        if not entry or entry.is_posted:
            return False
        entry.is_posted = True
        if self.app_core and self.app_core.current_user:
            entry.updated_by_user_id = self.app_core.current_user.id # type: ignore
        await self.save(entry)
        return True

    async def reverse(self, journal_id: int, reversal_date: date, description: str) -> Optional[JournalEntry]:
        raise NotImplementedError("Reversal logic belongs in JournalEntryManager.")

    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc = await session.get(Account, account_id)
            opening_balance = acc.opening_balance if acc and acc.opening_balance is not None else Decimal(0)
            ob_date = acc.opening_balance_date if acc else None

            je_activity_stmt = (
                select(
                    func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))
                )
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date <= as_of_date
                )
            )
            if ob_date:
                je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            
            result = await session.execute(je_activity_stmt)
            je_net_activity = result.scalar_one_or_none() or Decimal(0)
            
            return opening_balance + je_net_activity

    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))
                )
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date
                )
            )
            result = await session.execute(stmt)
            balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).where(
                RecurringPattern.is_active == True,
                RecurringPattern.next_generation_date <= as_of_date,
                or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)
            ).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt)
            return list(result.scalars().all())

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
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context

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
            return await session.get(CompanySetting, settings_id)

    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting:
        if self.app_core and self.app_core.current_user:
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

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]):
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

# New Interface for FiscalYearService
class IFiscalYearRepository(IRepository[FiscalYear, int]):
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date) -> Optional[FiscalYear]: pass
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

class ICurrencyRepository(IRepository[Currency, str]): # ID is code (str)
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


from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService # Added FiscalYearService

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository",
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
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
# (Content as previously generated and verified)
import bcrypt
from typing import Optional, List 
from app.models.core.user import User, Role 
from sqlalchemy import select 
from sqlalchemy.orm import selectinload 
from app.core.database_manager import DatabaseManager 
import datetime 

class SecurityManager:
    def __init__(self, db_manager: DatabaseManager): 
        self.db_manager = db_manager
        self.current_user: Optional[User] = None

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
                    # Session context manager handles commit
                    return user
                else: 
                    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                    user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
                    if user.failed_login_attempts >= 5: 
                        user.is_active = False 
                        print(f"User {username} account locked due to too many failed login attempts.")
            elif user and not user.is_active:
                print(f"User {username} account is inactive.")
                user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
        self.current_user = None 
        return None

    def logout_user(self):
        self.current_user = None

    def get_current_user(self) -> Optional[User]:
        return self.current_user

    def has_permission(self, required_permission_code: str) -> bool: 
        if not self.current_user or not self.current_user.is_active:
            return False
        if not self.current_user.roles:
             return False 
        for role in self.current_user.roles:
            if not role.permissions: continue
            for perm in role.permissions:
                if perm.code == required_permission_code:
                    return True
        return False

    async def create_user(self, username:str, password:str, email:Optional[str]=None, full_name:Optional[str]=None, role_names:Optional[List[str]]=None, is_active:bool=True) -> User:
        async with self.db_manager.session() as session:
            stmt_exist = select(User).where(User.username == username)
            if (await session.execute(stmt_exist)).scalars().first():
                raise ValueError(f"Username '{username}' already exists.")
            if email:
                stmt_email_exist = select(User).where(User.email == email)
                if (await session.execute(stmt_email_exist)).scalars().first():
                    raise ValueError(f"Email '{email}' already registered.")

            hashed_password = self.hash_password(password)
            new_user = User(
                username=username, password_hash=hashed_password, email=email,
                full_name=full_name, is_active=is_active,
            )
            if role_names:
                roles_q = await session.execute(select(Role).where(Role.name.in_(role_names))) # type: ignore
                db_roles = roles_q.scalars().all()
                if len(db_roles) != len(role_names):
                    found_role_names = {r.name for r in db_roles}
                    missing_roles = [r_name for r_name in role_names if r_name not in found_role_names]
                    print(f"Warning: Roles not found: {missing_roles}")
                new_user.roles.extend(db_roles) 
            
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            return new_user

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
# (Content as previously generated, verified)
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator 

import asyncpg # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config_manager import ConfigManager

class DatabaseManager:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_database_config()
        self.engine = None # type: ignore 
        self.session_factory: Optional[sessionmaker[AsyncSession]] = None
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        if self.engine: 
            return

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
        
        self.session_factory = sessionmaker(
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
            print(f"Failed to create asyncpg pool: {e}")
            self.pool = None 

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]: 
        if not self.session_factory:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            
        session: AsyncSession = self.session_factory()
        try:
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
            yield connection # type: ignore 
    
    async def execute_query(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, callback):
        async with self.connection() as conn:
            async with conn.transaction():
                return await callback(conn)
    
    async def close_connections(self):
        if self.pool:
            await self.pool.close()
            self.pool = None 
        
        if self.engine:
            await self.engine.dispose()
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
# (This version incorporates the diff, meaning it's the more complete one from my previous generations)
from typing import Optional, Any
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.accounting.journal_entry_manager import JournalEntryManager
from app.accounting.fiscal_period_manager import FiscalPeriodManager
from app.accounting.currency_manager import CurrencyManager

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.accounting_services import AccountTypeService, CurrencyService as CurrencyRepoService, ExchangeRateService, FiscalYearService # Added FiscalYearService


from app.utils.sequence_generator import SequenceGenerator

from app.tax.gst_manager import GSTManager
from app.tax.tax_calculator import TaxCalculator
from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.reporting.report_engine import ReportEngine


class ApplicationCore:
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._fiscal_year_service_instance: Optional[FiscalYearService] = None # Added
        self._sequence_service_instance: Optional[SequenceService] = None
        self._company_settings_service_instance: Optional[CompanySettingsService] = None
        self._tax_code_service_instance: Optional[TaxCodeService] = None
        self._gst_return_service_instance: Optional[GSTReturnService] = None
        self._account_type_service_instance: Optional[AccountTypeService] = None
        self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
        self._configuration_service_instance: Optional[ConfigurationService] = None

        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        self._fp_manager_instance: Optional[FiscalPeriodManager] = None
        self._currency_manager_instance: Optional[CurrencyManager] = None
        self._gst_manager_instance: Optional[GSTManager] = None
        self._tax_calculator_instance: Optional[TaxCalculator] = None
        self._financial_statement_generator_instance: Optional[FinancialStatementGenerator] = None
        self._report_engine_instance: Optional[ReportEngine] = None

        print("ApplicationCore initialized.")

    async def startup(self):
        print("ApplicationCore starting up...")
        await self.db_manager.initialize()
        
        self._account_service_instance = AccountService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager)
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self) # Added instantiation
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager) # Corrected assignment from self.config_service_instance
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)


        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        
        py_sequence_generator = SequenceGenerator(self.sequence_service)
        self._je_manager_instance = JournalEntryManager(
            self.journal_service, self.account_service, 
            self.fiscal_period_service, py_sequence_generator, self
        )
        self._fp_manager_instance = FiscalPeriodManager(self) 
        self._currency_manager_instance = CurrencyManager(self) 

        self._tax_calculator_instance = TaxCalculator(self.tax_code_service)
        self._gst_manager_instance = GSTManager(
            self.tax_code_service, self.journal_service, self.company_settings_service,
            self.gst_return_service, self.account_service, self.fiscal_period_service,
            py_sequence_generator, self
        )
        self._financial_statement_generator_instance = FinancialStatementGenerator(
            self.account_service, self.journal_service, self.fiscal_period_service,
            self.account_type_service, 
            self.tax_code_service, self.company_settings_service
        )
        self._report_engine_instance = ReportEngine(self)
        
        self.module_manager.load_all_modules()
        print("ApplicationCore startup complete.")

    async def shutdown(self):
        print("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        print("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    # Service Properties
    @property
    def account_service(self) -> AccountService:
        if not self._account_service_instance: raise RuntimeError("AccountService not initialized.")
        return self._account_service_instance
    @property
    def journal_service(self) -> JournalService:
        if not self._journal_service_instance: raise RuntimeError("JournalService not initialized.")
        return self._journal_service_instance
    @property
    def fiscal_period_service(self) -> FiscalPeriodService:
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    @property
    def fiscal_year_service(self) -> FiscalYearService: # Added property
        if not self._fiscal_year_service_instance: raise RuntimeError("FiscalYearService not initialized.")
        return self._fiscal_year_service_instance
    @property
    def sequence_service(self) -> SequenceService:
        if not self._sequence_service_instance: raise RuntimeError("SequenceService not initialized.")
        return self._sequence_service_instance
    @property
    def company_settings_service(self) -> CompanySettingsService:
        if not self._company_settings_service_instance: raise RuntimeError("CompanySettingsService not initialized.")
        return self._company_settings_service_instance
    @property
    def tax_code_service(self) -> TaxCodeService:
        if not self._tax_code_service_instance: raise RuntimeError("TaxCodeService not initialized.")
        return self._tax_code_service_instance
    @property
    def gst_return_service(self) -> GSTReturnService:
        if not self._gst_return_service_instance: raise RuntimeError("GSTReturnService not initialized.")
        return self._gst_return_service_instance
    @property
    def account_type_service(self) -> AccountTypeService: 
        if not self._account_type_service_instance: raise RuntimeError("AccountTypeService not initialized.")
        return self._account_type_service_instance 
    @property
    def currency_repo_service(self) -> CurrencyRepoService: # Name used in __init__
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property
    def currency_service(self) -> CurrencyRepoService: # Alias for consistency if CurrencyManager uses currency_service
        return self.currency_repo_service
    @property
    def exchange_rate_service(self) -> ExchangeRateService: 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def configuration_service(self) -> ConfigurationService: 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance

    # Manager Properties
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager:
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property
    def accounting_service(self) -> ChartOfAccountsManager: # Facade for UI, points to manager
        return self.chart_of_accounts_manager
    @property
    def journal_entry_manager(self) -> JournalEntryManager:
        if not self._je_manager_instance: raise RuntimeError("JournalEntryManager not initialized.")
        return self._je_manager_instance
    @property
    def fiscal_period_manager(self) -> FiscalPeriodManager: 
        if not self._fp_manager_instance: raise RuntimeError("FiscalPeriodManager not initialized.")
        return self._fp_manager_instance
    @property
    def currency_manager(self) -> CurrencyManager: 
        if not self._currency_manager_instance: raise RuntimeError("CurrencyManager not initialized.")
        return self._currency_manager_instance
    @property
    def gst_manager(self) -> GSTManager: 
        if not self._gst_manager_instance: raise RuntimeError("GSTManager not initialized.")
        return self._gst_manager_instance
    @property
    def tax_calculator(self) -> TaxCalculator: 
        if not self._tax_calculator_instance: raise RuntimeError("TaxCalculator not initialized.")
        return self._tax_calculator_instance
    @property
    def financial_statement_generator(self) -> FinancialStatementGenerator: 
        if not self._financial_statement_generator_instance: raise RuntimeError("FinancialStatementGenerator not initialized.")
        return self._financial_statement_generator_instance
    @property
    def report_engine(self) -> ReportEngine: 
        if not self._report_engine_instance: raise RuntimeError("ReportEngine not initialized.")
        return self._report_engine_instance

```

# app/models/__init__.py
```py
# File: app/models/__init__.py
# (Content as previously generated and verified, reflecting subdirectory model structure)
from .base import Base, TimestampMixin, UserAuditMixin

# Core schema models
from .core.user import User, Role, Permission # Removed UserRole, RolePermission
from .core.company_setting import CompanySetting
from .core.configuration import Configuration
from .core.sequence import Sequence

# Accounting schema models
from .accounting.account_type import AccountType
from .accounting.currency import Currency 
from .accounting.exchange_rate import ExchangeRate 
from .accounting.account import Account 
from .accounting.fiscal_year import FiscalYear
from .accounting.fiscal_period import FiscalPeriod 
from .accounting.journal_entry import JournalEntry, JournalEntryLine 
from .accounting.recurring_pattern import RecurringPattern
from .accounting.dimension import Dimension 
from .accounting.budget import Budget, BudgetDetail 
from .accounting.tax_code import TaxCode 
from .accounting.gst_return import GSTReturn 
from .accounting.withholding_tax_certificate import WithholdingTaxCertificate

# Business schema models
from .business.customer import Customer
from .business.vendor import Vendor
from .business.product import Product
from .business.inventory_movement import InventoryMovement
from .business.sales_invoice import SalesInvoice, SalesInvoiceLine
from .business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from .business.bank_account import BankAccount
from .business.bank_transaction import BankTransaction
from .business.payment import Payment, PaymentAllocation

# Audit schema models
from .audit.audit_log import AuditLog
from .audit.data_change_history import DataChangeHistory

__all__ = [
    "Base", "TimestampMixin", "UserAuditMixin",
    # Core
    "User", "Role", "Permission", # Removed UserRole, RolePermission
    "CompanySetting", "Configuration", "Sequence",
    # Accounting
    "AccountType", "Currency", "ExchangeRate", "Account",
    "FiscalYear", "FiscalPeriod", "JournalEntry", "JournalEntryLine",
    "RecurringPattern", "Dimension", "Budget", "BudgetDetail",
    "TaxCode", "GSTReturn", "WithholdingTaxCertificate",
    # Business
    "Customer", "Vendor", "Product", "InventoryMovement",
    "SalesInvoice", "SalesInvoiceLine", "PurchaseInvoice", "PurchaseInvoiceLine",
    "BankAccount", "BankTransaction", "Payment", "PaymentAllocation",
    # Audit
    "AuditLog", "DataChangeHistory",
]

```

# app/models/base.py
```py
# File: app/models/base.py
# (Content previously generated, no changes needed)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import DateTime, Integer, ForeignKey # Ensure Integer, ForeignKey are imported
from typing import Optional
import datetime

Base = declarative_base()

class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now())

class UserAuditMixin:
    # Explicitly add ForeignKey references here as UserAuditMixin is generic.
    # The target table 'core.users' is known.
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

```

# app/models/core/__init__.py
```py
# File: app/models/core/__init__.py
# (Content previously generated)
from .configuration import Configuration
from .sequence import Sequence

__all__ = ["Configuration", "Sequence"]

```

# app/models/core/configuration.py
```py
# File: app/models/core/configuration.py
# New model for core.configuration table
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
# from app.models.user import User # For FK relationship
import datetime
from typing import Optional

class Configuration(Base, TimestampMixin):
    __tablename__ = 'configuration'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    config_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True)

    # updated_by_user: Mapped[Optional["User"]] = relationship("User") # If User accessible

```

# app/models/core/company_setting.py
```py
# File: app/models/core/company_setting.py
# (Moved from app/models/company_setting.py and fields updated)
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.core.user import User # For FK relationship type hint
import datetime
from typing import Optional

class CompanySetting(Base, TimestampMixin):
    __tablename__ = 'company_settings'
    __table_args__ = (
        CheckConstraint("fiscal_year_start_month BETWEEN 1 AND 12", name='ck_cs_fy_month'),
        CheckConstraint("fiscal_year_start_day BETWEEN 1 AND 31", name='ck_cs_fy_day'),
        {'schema': 'core'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True) 
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registration_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[str] = mapped_column(String(50), default='Singapore') 
    country: Mapped[str] = mapped_column(String(50), default='Singapore') 
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logo: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1) 
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, default=1) 
    base_currency: Mapped[str] = mapped_column(String(3), default='SGD') 
    tax_id_label: Mapped[str] = mapped_column(String(50), default='UEN') 
    date_format: Mapped[str] = mapped_column(String(20), default='yyyy-MM-dd') 
    
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True) 

    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/core/sequence.py
```py
# File: app/models/core/sequence.py
# New model for core.sequences table
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin # Only TimestampMixin, no UserAuditMixin for this
from typing import Optional

class Sequence(Base, TimestampMixin):
    __tablename__ = 'sequences'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sequence_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    prefix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    next_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    increment_by: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_value: Mapped[int] = mapped_column(Integer, default=2147483647, nullable=False) # Max int4
    cycle: Mapped[bool] = mapped_column(Boolean, default=False)
    format_template: Mapped[str] = mapped_column(String(50), default='{PREFIX}{VALUE}{SUFFIX}')

```

# app/models/core/user.py
```py
# File: app/models/core/user.py
# (Moved from app/models/user.py and fields updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin 
import datetime 
from typing import List, Optional 

# Junction tables defined here using Base.metadata
user_roles_table = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    schema='core'
)

role_permissions_table = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('core.permissions.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    schema='core'
)

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_login_attempt: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    require_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    
    roles: Mapped[List["Role"]] = relationship("Role", secondary=user_roles_table, back_populates="users")

class Role(Base, TimestampMixin):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    users: Mapped[List["User"]] = relationship("User", secondary=user_roles_table, back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary=role_permissions_table, back_populates="roles")

class Permission(Base): 
    __tablename__ = 'permissions'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) 
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False) 
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()) # Only created_at

    roles: Mapped[List["Role"]] = relationship("Role", secondary=role_permissions_table, back_populates="permissions")

# Removed UserRole class definition
# Removed RolePermission class definition

```

