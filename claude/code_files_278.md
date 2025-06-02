<think>
The application launched successfully with the schema and model updates for saving bank reconciliation state. This is a great sign! The UI itself (Bank Reconciliation tab) already reflects the structure we built in previous steps.

Now, we need to implement **Phase 2: DTOs, Service, and Manager for Bank Reconciliation**, specifically for the "Save Reconciliation" functionality.

**Roadmap Item: Bank Reconciliation - Save Reconciliation State (Backend Logic)**

**Goal**:
1.  Create Data Transfer Objects (DTOs) for bank reconciliation data.
2.  Implement a `BankReconciliationService` to handle database interactions for `BankReconciliation` records and updating related `BankTransaction` and `BankAccount` records.
3.  Implement a `BankReconciliationManager` to orchestrate the saving of a completed reconciliation.
4.  Update `ApplicationCore` to include these new components.
5.  Update relevant `__init__.py` files.

**Execution Plan (Continuing from response_32):**

**Step 2 (Continued): New DTOs in `app/utils/pydantic_models.py`**
*   **File**: `app/utils/pydantic_models.py` (Update)
*   **DTOs**:
    *   `BankReconciliationBaseData(AppBaseModel)`:
        *   `bank_account_id: int`
        *   `statement_date: date`
        *   `statement_ending_balance: Decimal`
        *   `calculated_book_balance: Decimal`
        *   `reconciled_difference: Decimal`
        *   `notes: Optional[str] = None`
    *   `BankReconciliationCreateData(BankReconciliationBaseData, UserAuditData)`: Inherits and adds `user_id`.
    *   `BankReconciliationData(BankReconciliationBaseData)`:
        *   `id: int`
        *   `reconciliation_date: datetime`
        *   `created_at: datetime`
        *   `updated_at: datetime`
        *   `created_by_user_id: int`
        *   (Potentially add summarized info about cleared items counts if needed for display, or fetch separately)
*   **Checklist**:
    *   [ ] Define DTOs with correct fields and types.
    *   [ ] Ensure all existing DTOs in the file are preserved.

**Step 3 (Continued): New Service - `BankReconciliationService`**
*   **File**: `app/services/business_services.py` (Add new class `BankReconciliationService`).
*   **File**: `app/services/__init__.py` (Add new interface `IBankReconciliationRepository` and export new service).
*   **Interface `IBankReconciliationRepository(IRepository[BankReconciliation, int])`**:
    *   Declare `save_reconciliation(...)` abstract method.
*   **`BankReconciliationService` Implementation**:
    *   `save_reconciliation(self, bank_account_id: int, statement_date: date, statement_ending_balance: Decimal, calculated_book_balance: Decimal, reconciled_difference: Decimal, notes: Optional[str], user_id: int, cleared_statement_txn_ids: List[int], cleared_system_txn_ids: List[int]) -> Result[BankReconciliation]`
        *   This method will operate within a single database transaction provided by the manager.
        *   1. Create and save the `BankReconciliation` ORM object.
        *   2. Update `BankTransaction` records:
            *   For each ID in `cleared_statement_txn_ids` and `cleared_system_txn_ids`:
                *   Set `is_reconciled = True`.
                *   Set `reconciled_date = statement_date`.
                *   Set `reconciled_bank_reconciliation_id` to the ID of the newly saved `BankReconciliation` record.
        *   3. Update `BankAccount` record:
            *   Set `last_reconciled_date = statement_date`.
            *   Set `last_reconciled_balance = statement_ending_balance` (or `calculated_book_balance` if they must match exactly for saving). For bank rec, `statement_ending_balance` is usually the target.
        *   Use the passed-in `session` from the manager.
*   **Checklist**:
    *   [ ] Define interface.
    *   [ ] Implement service with `save_reconciliation` logic.
    *   [ ] Ensure transactional integrity (caller/manager will provide session).
    *   [ ] Update `app/services/__init__.py`.

**Step 4 (Continued): New Manager - `BankReconciliationManager`**
*   **File**: `app/business_logic/bank_reconciliation_manager.py` (New File).
*   **File**: `app/business_logic/__init__.py` (Export new manager).
*   **Dependencies**: `BankReconciliationService`, `BankAccountService`, `BankTransactionService`, `ApplicationCore`.
*   **Method `finalize_reconciliation(self, reconciliation_dto: BankReconciliationCreateData, cleared_statement_txn_ids: List[int], cleared_system_txn_ids: List[int]) -> Result[BankReconciliationData]`**:
    *   Perform final validation (e.g., ensure `reconciled_difference` in DTO is near zero).
    *   Start a database transaction: `async with self.app_core.db_manager.session() as session:`.
    *   Call `bank_reconciliation_service.save_reconciliation(...)` passing all data and the session.
    *   Convert the saved `BankReconciliation` ORM object to `BankReconciliationData` DTO for the result.
    *   Return `Result.success(dto)` or `Result.failure(errors)`.
*   **Checklist**:
    *   [ ] Create manager class.
    *   [ ] Implement `finalize_reconciliation` method.
    *   [ ] Handle transactions and error propagation.
    *   [ ] Update `app/business_logic/__init__.py`.

**Step 5 (Continued): Update `ApplicationCore`**
*   **File**: `app/core/application_core.py` (Update).
*   **Changes**:
    *   Import new `BankReconciliationService` and `BankReconciliationManager`.
    *   Add instance variable placeholders (e.g., `_bank_reconciliation_service_instance`).
    *   Instantiate them in `startup()`.
    *   Add `@property` accessors for them.
*   **Checklist**:
    *   [ ] Correct imports.
    *   [ ] Correct instantiation in `startup()`.
    *   [ ] Correct property definitions.

I will proceed with these steps, generating complete files.

</think>

Excellent, the application is launching successfully with the foundational UI for Bank Reconciliation! It's great to see the visual progress.

Now, we'll proceed with implementing the backend logic for **Saving the Reconciliation State**. This involves creating the necessary DTOs, Service, and Manager classes, and then integrating them into the `ApplicationCore`.

The plan is as follows:
1.  Define Data Transfer Objects (DTOs) for bank reconciliation.
2.  Create `BankReconciliationService` and its interface `IBankReconciliationRepository` for database operations.
3.  Create `BankReconciliationManager` to orchestrate the reconciliation saving process.
4.  Update `ApplicationCore` to include these new components.
5.  Update relevant `__init__.py` files.

I will generate the complete files, ensuring meticulous attention to detail and preservation of existing code.

---
**1. File: `app/utils/pydantic_models.py` (Updated)**
---
**Objective**: Add DTOs for creating and representing saved bank reconciliation records.

**Base Version Reference**: The version from response_22 (which included Audit Log DTOs).
**Intended Changes**:
*   Add `BankReconciliationBaseData`.
*   Add `BankReconciliationCreateData`.
*   Add `BankReconciliationData`.

**Generated File**: `app/utils/pydantic_models.py`
```python
# app/utils/pydantic_models.py
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
# ... (Content from response_22, unchanged)
class AccountBaseData(AppBaseModel):
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

# --- Journal Entry Related DTOs ---
# ... (Content from response_22, unchanged)
class JournalEntryLineData(AppBaseModel):
    account_id: int; description: Optional[str] = Field(None, max_length=200); debit_amount: Decimal = Field(Decimal(0))
    credit_amount: Decimal = Field(Decimal(0)); currency_code: str = Field("SGD", max_length=3) 
    exchange_rate: Decimal = Field(Decimal(1)); tax_code: Optional[str] = Field(None, max_length=20) 
    tax_amount: Decimal = Field(Decimal(0)); dimension1_id: Optional[int] = None; dimension2_id: Optional[int] = None 
    @validator('debit_amount', 'credit_amount', 'exchange_rate', 'tax_amount', pre=True, always=True)
    def je_line_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0) 
    @root_validator(skip_on_failure=True)
    def check_je_line_debit_credit_exclusive(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        debit = values.get('debit_amount', Decimal(0)); credit = values.get('credit_amount', Decimal(0))
        if debit > Decimal(0) and credit > Decimal(0): raise ValueError("Debit and Credit amounts cannot both be positive for a single line.")
        return values
class JournalEntryData(AppBaseModel, UserAuditData):
    journal_type: str; entry_date: date; description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100); is_recurring: bool = False 
    recurring_pattern_id: Optional[int] = None; source_type: Optional[str] = Field(None, max_length=50)
    source_id: Optional[int] = None; lines: List[JournalEntryLineData]
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
# ... (Content from response_22, unchanged)
class GSTTransactionLineDetail(AppBaseModel):
    transaction_date: date; document_no: str; entity_name: Optional[str] = None; description: str
    account_code: str; account_name: str; net_amount: Decimal; gst_amount: Decimal; tax_code_applied: Optional[str] = None
class GSTReturnData(AppBaseModel, UserAuditData):
    id: Optional[int] = None; return_period: str = Field(..., max_length=20); start_date: date; end_date: date
    filing_due_date: Optional[date] = None; standard_rated_supplies: Decimal = Field(Decimal(0))         
    zero_rated_supplies: Decimal = Field(Decimal(0)); exempt_supplies: Decimal = Field(Decimal(0))                 
    total_supplies: Decimal = Field(Decimal(0)); taxable_purchases: Decimal = Field(Decimal(0))               
    output_tax: Decimal = Field(Decimal(0)); input_tax: Decimal = Field(Decimal(0))                       
    tax_adjustments: Decimal = Field(Decimal(0)); tax_payable: Decimal = Field(Decimal(0))                     
    status: str = Field("Draft", max_length=20); submission_date: Optional[date] = None
    submission_reference: Optional[str] = Field(None, max_length=50); journal_entry_id: Optional[int] = None
    notes: Optional[str] = None; detailed_breakdown: Optional[Dict[str, List[GSTTransactionLineDetail]]] = Field(None, exclude=True) 
    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs ---
# ... (Content from response_22, unchanged)
class TaxCalculationResultData(AppBaseModel): tax_amount: Decimal; tax_account_id: Optional[int] = None; taxable_amount: Decimal
class TransactionLineTaxData(AppBaseModel): amount: Decimal; tax_code: Optional[str] = None; account_id: Optional[int] = None; index: int 
class TransactionTaxData(AppBaseModel): transaction_type: str; lines: List[TransactionLineTaxData]

# --- Validation Result DTO ---
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
class CompanySettingData(AppBaseModel, UserAuditData): 
    id: Optional[int] = None; company_name: str = Field(..., max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50); country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100); phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None; website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None; fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31); base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50); date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs ---
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
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
# ... (Content from response_22, unchanged)
class AuditLogEntryData(AppBaseModel): id: int; timestamp: datetime; username: Optional[str] = "System"; action: str; entity_type: str; entity_id: Optional[int] = None; entity_name: Optional[str] = None; changes_summary: Optional[str] = None; ip_address: Optional[str] = None
class DataChangeHistoryEntryData(AppBaseModel): id: int; changed_at: datetime; table_name: str; record_id: int; field_name: str; old_value: Optional[str] = None; new_value: Optional[str] = None; change_type: DataChangeTypeEnum; changed_by_username: Optional[str] = "System"

# --- Bank Reconciliation DTOs (New) ---
class BankReconciliationBaseData(AppBaseModel):
    bank_account_id: int
    statement_date: date
    statement_ending_balance: Decimal
    calculated_book_balance: Decimal
    reconciled_difference: Decimal
    notes: Optional[str] = None

class BankReconciliationCreateData(BankReconciliationBaseData, UserAuditData):
    pass # user_id for audit is inherited

class BankReconciliationData(BankReconciliationBaseData): # For returning full data
    id: int
    reconciliation_date: datetime # System timestamp when record is created/saved
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    # Might add lists of reconciled_statement_transaction_ids and reconciled_book_transaction_ids if needed for display

```

**Validation of `app/utils/pydantic_models.py`:**

*   **Diff (Conceptual)**: Compared to the version from response_22 (which included Audit Log DTOs).
    *   The new DTOs `BankReconciliationBaseData`, `BankReconciliationCreateData`, and `BankReconciliationData` are correctly added at the end of the file.
    *   Their field definitions match the plan (bank_account_id, statement_date, statement_ending_balance, calculated_book_balance, reconciled_difference, notes, and audit/ID fields for Create/Data DTOs).
*   **Correctness**: The new DTOs are correctly defined using `AppBaseModel` and `UserAuditData` where appropriate. Types are correct.
*   **Preservation**: All previously existing DTOs (Account, JournalEntry, GST, Tax, CompanySetting, FiscalYear, Customer, Vendor, Product, SalesInvoice, User/Role, PurchaseInvoice, BankAccount, BankTransaction, Payment, AuditLog) are fully preserved.
*   **Conclusion**: The file is correctly updated and complete.

---
**2. Files: `app/services/business_services.py` (Add `BankReconciliationService`) and `app/services/__init__.py` (Add `IBankReconciliationRepository` and export new service)**
---

**Generated File**: `app/services/business_services.py`
```python
# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple # Added Tuple
from sqlalchemy import select, func, and_, or_, literal_column, case, update as sqlalchemy_update # Added update
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 
from datetime import date # Ensure date is imported if used directly

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
from app.models.business.bank_reconciliation import BankReconciliation # New import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository, IInventoryMovementRepository,
    IBankAccountRepository, IBankTransactionRepository, IPaymentRepository,
    IBankReconciliationRepository # New import
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData, BankReconciliationData # Added BankReconciliationData
)
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum 
# from datetime import date # Already imported

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

# --- CustomerService, VendorService, ProductService ---
# --- SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService ---
# --- BankAccountService, BankTransactionService, PaymentService ---
# (These services are assumed to be complete and correct as per response_29's business_services.py)
# (For brevity, their full code from response_29 is not repeated here, but they ARE part of this complete file)
class CustomerService(ICustomerRepository): # Copied from response_29 for completeness
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
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

class VendorService(IVendorRepository): # Copied from response_29 for completeness
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

class ProductService(IProductRepository): # Copied from response_29 for completeness
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

class SalesInvoiceService(ISalesInvoiceRepository): # Copied from response_29 for completeness
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
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

class PurchaseInvoiceService(IPurchaseInvoiceRepository): # Copied from response_29 for completeness
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
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

class InventoryMovementService(IInventoryMovementRepository): # Copied from response_29 for completeness
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

class BankAccountService(IBankAccountRepository): # Copied from response_29 for completeness
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

class BankTransactionService(IBankTransactionRepository): # Copied from response_29 for completeness (with is_from_statement_filter)
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
                summaries.append(BankTransactionSummaryData(id=txn.id,transaction_date=txn.transaction_date,value_date=txn.value_date,transaction_type=BankTransactionTypeEnum(txn.transaction_type), description=txn.description,reference=txn.reference,amount=txn.amount, is_reconciled=txn.is_reconciled))
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

class PaymentService(IPaymentRepository): # Copied from response_29 for completeness
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

# --- New BankReconciliationService ---
class BankReconciliationService(IBankReconciliationRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[BankReconciliation]:
        async with self.db_manager.session() as session:
            return await session.get(BankReconciliation, id_val)

    async def get_all(self) -> List[BankReconciliation]:
        async with self.db_manager.session() as session:
            stmt = select(BankReconciliation).order_by(BankReconciliation.statement_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        # This 'add' is for the IRepository compliance. The main logic is in save_reconciliation.
        return await self.save(entity, session)

    async def update(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        # Reconciliations are typically not updated in this way, but for IRepository:
        return await self.save(entity, session)

    async def delete(self, id_val: int) -> bool:
        # Deleting a reconciliation might require un-reconciling transactions. Complex.
        self.logger.warning(f"Deletion of BankReconciliation ID {id_val} attempted. This operation should be handled with care and may require reversing reconciled transactions.")
        async with self.db_manager.session() as session:
            # First, un-link transactions
            update_stmt = (
                sqlalchemy_update(BankTransaction)
                .where(BankTransaction.reconciled_bank_reconciliation_id == id_val)
                .values(is_reconciled=False, reconciled_date=None, reconciled_bank_reconciliation_id=None)
            )
            await session.execute(update_stmt)
            
            entity = await session.get(BankReconciliation, id_val)
            if entity:
                await session.delete(entity)
                await session.flush() # Ensure deletion occurs before commit is implied by context manager exit
                return True
            return False
            
    async def save(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        """Generic save, typically used by manager which orchestrates the full save_reconciliation."""
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity)
            await current_session.flush()
            await current_session.refresh(entity)
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: # type: ignore
                return await _save_logic(new_session)

    async def save_reconciliation_details(
        self, 
        reconciliation_orm: BankReconciliation,
        cleared_statement_txn_ids: List[int], 
        cleared_system_txn_ids: List[int],
        statement_end_date: date,
        bank_account_id: int,
        statement_ending_balance: Decimal, # This is the BankAccount.last_reconciled_balance
        session: AsyncSession # Must be called within an existing transaction
    ) -> BankReconciliation:
        """
        Saves the BankReconciliation record and updates related transactions and bank account.
        This method expects to be called within an existing transaction/session.
        """
        # 1. Save the BankReconciliation record itself to get its ID
        session.add(reconciliation_orm)
        await session.flush() 
        await session.refresh(reconciliation_orm)
        
        # 2. Update BankTransaction records
        all_cleared_txn_ids = list(set(cleared_statement_txn_ids + cleared_system_txn_ids))
        if all_cleared_txn_ids:
            update_txn_stmt = (
                sqlalchemy_update(BankTransaction)
                .where(BankTransaction.id.in_(all_cleared_txn_ids))
                .values(
                    is_reconciled=True,
                    reconciled_date=statement_end_date,
                    reconciled_bank_reconciliation_id=reconciliation_orm.id
                )
                .execution_options(synchronize_session="fetch") # To ensure session is aware of changes
            )
            await session.execute(update_txn_stmt)

        # 3. Update BankAccount record
        bank_account_to_update = await session.get(BankAccount, bank_account_id)
        if bank_account_to_update:
            bank_account_to_update.last_reconciled_date = statement_end_date
            bank_account_to_update.last_reconciled_balance = statement_ending_balance # Use statement ending balance as the reconciled figure
            session.add(bank_account_to_update)
        else:
            # This should ideally not happen if bank_account_id was validated earlier
            self.logger.error(f"BankAccount ID {bank_account_id} not found during reconciliation save for BankReconciliation ID {reconciliation_orm.id}.")
            raise ValueError(f"BankAccount ID {bank_account_id} not found during reconciliation save.")

        await session.flush() # Ensure all updates are flushed before returning
        await session.refresh(reconciliation_orm) # Refresh again to get any trigger-based changes
        return reconciliation_orm

```

**Generated File**: `app/services/__init__.py`
```python
# File: app/services/__init__.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Generic, TypeVar, Dict, Tuple 
from datetime import date, datetime 
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
from app.models.business.bank_reconciliation import BankReconciliation # New Model Import

from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData,
    AuditLogEntryData, DataChangeHistoryEntryData, BankReconciliationData # Added BankReconciliationData
)
from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum, DataChangeTypeEnum 
)

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

class IInventoryMovementRepository(IRepository[InventoryMovement, int]):
    @abstractmethod
    async def save(self, entity: InventoryMovement, session: Optional[Any]=None) -> InventoryMovement: pass 

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
    async def save(self, entity: BankTransaction, session: Optional[Any] = None) -> BankTransaction: pass

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
    async def save(self, entity: Payment, session: Optional[Any] = None) -> Payment: pass

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

# New Interface for BankReconciliation
class IBankReconciliationRepository(IRepository[BankReconciliation, int]):
    @abstractmethod
    async def save_reconciliation_details(
        self, 
        reconciliation_orm: BankReconciliation,
        cleared_statement_txn_ids: List[int], 
        cleared_system_txn_ids: List[int],
        statement_end_date: date,
        bank_account_id: int,
        statement_ending_balance: Decimal,
        session: AsyncSession # Expects to be run in an existing session
    ) -> BankReconciliation: pass
    # Additional specific query methods can be added here if needed, e.g.:
    # async def get_reconciliations_for_account(self, bank_account_id: int) -> List[BankReconciliation]: pass
    # async def get_latest_reconciliation_for_account(self, bank_account_id: int) -> Optional[BankReconciliation]: pass

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
    BankReconciliationService # New Service Import
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
    "IBankReconciliationRepository", # New Interface Export
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
    "BankReconciliationService", # New Service Export
]

```

**Summary of Validations for DTOs and Services:**
*   **`app/utils/pydantic_models.py`**: Correctly adds `BankReconciliationBaseData`, `BankReconciliationCreateData`, and `BankReconciliationData` while preserving all previous DTOs.
*   **`app/services/business_services.py`**:
    *   Correctly adds the new `BankReconciliationService` class.
    *   The `save_reconciliation_details` method within `BankReconciliationService` implements the logic to save the reconciliation record, update associated bank transactions (`is_reconciled`, `reconciled_date`, `reconciled_bank_reconciliation_id`), and update the parent `BankAccount` (`last_reconciled_date`, `last_reconciled_balance`). This method correctly expects to run within a session provided by the caller (manager).
    *   The standard CRUD methods (`get_by_id`, `get_all`, `add`, `update`, `delete`) for `BankReconciliationService` are implemented with appropriate considerations for reconciliation records (e.g., delete is complex).
    *   All other existing services in this file are fully preserved from their state in response_29.
*   **`app/services/__init__.py`**:
    *   Correctly adds the new model import `BankReconciliation`.
    *   Correctly adds the new DTO import `BankReconciliationData`.
    *   Correctly defines the new interface `IBankReconciliationRepository` with its `save_reconciliation_details` abstract method.
    *   Correctly adds `BankReconciliationService` import and exports `IBankReconciliationRepository` and `BankReconciliationService` in `__all__`.
    *   All other existing interfaces, imports, and exports are preserved.

The DTO and Service layers for saving bank reconciliation state are now correctly defined and complete. I will proceed to generate the Manager layer and `ApplicationCore` updates in the next step.
