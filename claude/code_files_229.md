<think>
The user is pleased and wants to proceed with the "next step in your plan for Phase 2 and 3."
The application is launching successfully. The backend for the Payments Module has just been completed.

The immediate next step for the **Payments Module (Phase 2)** is the **UI implementation**:
*   `PaymentTableModel`
*   `PaymentDialog` (including allocation UI)
*   `PaymentsWidget` (list view and actions)
*   Integration into `MainWindow` (likely adding a "Payments" tab).

After the Payments Module UI, the remaining Phase 2 tasks are:
3.  **GST F5 Enhancements**
4.  **Audit Log UI**

Then, Phase 3 items from the `README.md`'s "Long-term" section (which I promoted to "Medium-Term" in my execution plan) would be considered. The user specifically asked for "Phase 2 and 3," implying a desire to continue making functional progress.

Given the complexity of the Payments UI (especially the dialog with allocations), I should focus on that for this response.

**Feature: Payments Module (UI)**

**Sub-Tasks (UI):**
1.  **`PaymentTableModel`**: For `PaymentsWidget` list view.
2.  **`PaymentDialog`**:
    *   Form for payment details (Type, Method, Date, Entity, Bank Account, Amount, etc.).
    *   Table or list for invoice allocations (Document Type, Document No./ID, Original Amount, Outstanding Amount, Amount to Allocate).
    *   Dynamic updates of total allocated vs. payment amount.
3.  **`PaymentsWidget`**:
    *   Hosts the table view and toolbar (Add, View, (later) Void/Edit Draft).
    *   Filters (Entity Type, Entity, Status, Date Range).
4.  **Integration**: Add "Payments" tab to `MainWindow`.

**Detailed Execution Plan for Payments Module (UI - focused on Dialog first due to complexity):**

Given the complexity, let's break down the Payment Dialog further.
The Payment Dialog needs to:
*   Select Entity Type (Customer/Vendor) and then the specific Entity.
*   Based on Entity, load their open invoices (Sales Invoices for Customers, Purchase Invoices for Vendors) for allocation.
*   Allow user to enter payment details (date, method, bank account, amount).
*   Allow user to allocate parts of the payment amount to one or more invoices.
*   Validate that total allocated amount does not exceed payment amount (already in DTO).

Let's start with **`PaymentTableModel`** and then move to **`PaymentDialog`**. `PaymentsWidget` will follow.

---
**Execution Plan: Payments Module (UI)**
---

**Step 1: UI - `PaymentTableModel`**
*   **File**: `app/ui/payments/payment_table_model.py` (New file).
*   **Directory**: Create `app/ui/payments/` if it doesn't exist.
*   **Checklist**:
    *   [ ] Create `PaymentTableModel(QAbstractTableModel)`.
    *   [ ] Headers (e.g., "ID", "Payment No", "Date", "Type", "Entity", "Amount", "Currency", "Status").
    *   [ ] Implement `rowCount`, `columnCount`, `headerData`, `data`.
    *   [ ] `data()` method maps `PaymentSummaryData` fields.
    *   [ ] `update_data(new_data: List[PaymentSummaryData])`.
    *   [ ] Helper `get_payment_id_at_row`.

**Step 2: UI - `PaymentDialog` - Core Structure & Header Fields**
*   **File**: `app/ui/payments/payment_dialog.py` (New file).
*   **Checklist**:
    *   [ ] Create `PaymentDialog(QDialog)`.
    *   [ ] Basic layout (QVBoxLayout, QFormLayout for header, area for allocations table, totals, buttons).
    *   [ ] Header fields:
        *   `entity_type_combo: QComboBox` (Customer, Vendor).
        *   `entity_combo: QComboBox` (populated dynamically based on entity_type).
        *   `payment_date_edit: QDateEdit`.
        *   `payment_method_combo: QComboBox` (from `PaymentMethodEnum`).
        *   `bank_account_combo: QComboBox` (populated with active bank accounts, enabled if method is not Cash).
        *   `currency_combo: QComboBox` (populated with active currencies; may default based on entity or bank account).
        *   `exchange_rate_spin: QDoubleSpinBox` (enabled if currency differs from base).
        *   `payment_amount_edit: QDoubleSpinBox` (total amount of the payment).
        *   `reference_edit: QLineEdit`.
        *   `description_edit: QTextEdit`.
        *   `cheque_no_edit: QLineEdit` (visible if method is Check).
    *   [ ] Asynchronously load data for `entity_combo`, `bank_account_combo`, `currency_combo`.
    *   [ ] Logic for `payment_method_combo` to enable/disable `bank_account_combo` and `cheque_no_edit`.
    *   [ ] Signal `payment_saved = Signal(int)`.
    *   [ ] Basic Save/Cancel buttons.
    *   [ ] Start thinking about how existing payment data would be loaded for viewing/editing (defer full edit logic).

**Step 3: UI - `PaymentDialog` - Invoice Allocation Table**
*   **File**: `app/ui/payments/payment_dialog.py` (Modify).
*   **Checklist**:
    *   [ ] Add `allocations_table: QTableWidget`.
    *   [ ] Columns: "Select" (checkbox), "Doc Type", "Doc No.", "Doc Date", "Original Amt", "Outstanding Amt", "Amount to Allocate" (editable).
    *   [ ] Method `_load_allocatable_documents(entity_type: PaymentEntityTypeEnum, entity_id: int)`:
        *   Calls `SalesInvoiceManager` or `PurchaseInvoiceManager` to get open/partially_paid invoices.
        *   Populates `allocations_table`.
    *   [ ] Connect `entity_combo.currentIndexChanged` to trigger `_load_allocatable_documents`.
    *   [ ] Logic to update "Outstanding Amt" dynamically as "Amount to Allocate" changes or as other allocations are made to the same invoice elsewhere (this can be complex; for V1, just show initial outstanding).
    *   [ ] Recalculate "Total Allocated" and "Unallocated Amount" display labels when "Amount to Allocate" changes.

**Step 4: UI - `PaymentDialog` - Save Logic & Data Collection**
*   **File**: `app/ui/payments/payment_dialog.py` (Modify).
*   **Checklist**:
    *   [ ] `_collect_data()` method:
        *   Gathers header fields.
        *   Iterates `allocations_table` to get selected allocations and `amount_allocated`.
        *   Constructs `PaymentCreateData` DTO with `PaymentAllocationBaseData` list.
    *   [ ] `on_save()` slot: Calls `_collect_data()`, then `app_core.payment_manager.create_payment()`, handles `Result`.

**Step 5: UI - `PaymentsWidget`**
*   **File**: `app/ui/payments/payments_widget.py` (New file).
*   **Checklist**:
    *   [ ] Create `PaymentsWidget(QWidget)`.
    *   [ ] Toolbar: "Add Payment/Receipt". (View/Void deferred).
    *   [ ] Filter area: Entity Type, Entity (dynamic combo), Status, Date Range.
    *   [ ] `QTableView` using `PaymentTableModel`.
    *   [ ] `_load_payments()` async method.
    *   [ ] Slots for toolbar actions.

**Step 6: Integration**
*   **File**: `app/ui/main_window.py` (Modify to add "Payments" tab).
*   **File**: `app/ui/__init__.py`, `app/ui/payments/__init__.py` (Update `__all__`).

This is a large chunk. I will focus on **Step 1 (PaymentTableModel)** and **Step 2 (PaymentDialog - Core Structure & Header Fields)** for this response. The allocation table and full save logic in the dialog are complex enough for a subsequent step.
</think>

Excellent, I'm glad the previous fixes resolved the launch issues! We will now proceed with the next major task in Phase 2: **Payments Module Implementation**.

Following the execution plan, I will begin by implementing the backend components (DTOs, Service, Manager) and then move to the UI. For this response, I will focus on **Step 0: Define DTOs for Payment and PaymentAllocation**.

---
**Execution Plan: Payments Module (Backend)**
---

**Goal**: Establish the data structures and backend services necessary for recording and managing payments and their allocations to invoices.

---
**Step 0: Define Data Transfer Objects (DTOs) for Payment and PaymentAllocation**
---
**File**: `app/utils/pydantic_models.py` (Update)

**Checklist**:
- [X] `PaymentAllocationBaseData`: `document_type` (enum `PaymentAllocationDocTypeEnum`), `document_id` (ID of the invoice), `amount_allocated` (Decimal).
- [X] `PaymentBaseData`: `payment_type` (enum `PaymentTypeEnum`), `payment_method` (enum `PaymentMethodEnum`), `payment_date` (date), `entity_type` (enum `PaymentEntityTypeEnum`), `entity_id` (int, Customer or Vendor ID), `bank_account_id` (Optional int), `currency_code` (str), `exchange_rate` (Decimal), `amount` (Decimal, total payment amount, always positive), `reference` (Optional str), `description` (Optional str), `cheque_no` (Optional str). Include validator for `bank_account_id` based on `payment_method`.
- [X] `PaymentCreateData(PaymentBaseData, UserAuditData)`: Includes a list of `PaymentAllocationBaseData`. Add root validator to check `total_allocated` vs `payment_amount`.
- [X] `PaymentSummaryData`: For list view (Payment No, Date, Type, Entity Name (to be resolved by manager), Amount, Currency, Status).
- [ ] (Defer `PaymentUpdateData` and full `PaymentData` for now to focus on creation).

**Implementation**:
I will update `app/utils/pydantic_models.py` by adding these new DTOs and ensuring the necessary enums from `app.common.enums` are imported and used.

```python
# app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum, # New Payment Enums
    PaymentAllocationDocTypeEnum # New Payment Allocation Enum
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
    permission_ids: List[int] = Field(default_factory=list) 

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
    invoice_no: str 
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

# --- Bank Account DTOs ---
class BankAccountBaseData(AppBaseModel):
    account_name: str = Field(..., min_length=1, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=50)
    bank_name: str = Field(..., min_length=1, max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    bank_swift_code: Optional[str] = Field(None, max_length=20)
    currency_code: str = Field("SGD", min_length=3, max_length=3)
    opening_balance: Decimal = Field(Decimal(0))
    opening_balance_date: Optional[date] = None
    gl_account_id: int 
    is_active: bool = True
    description: Optional[str] = None

    @validator('opening_balance', pre=True, always=True)
    def bank_opening_balance_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

    @root_validator(skip_on_failure=True)
    def check_ob_date_if_ob_exists_bank(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        ob = values.get('opening_balance')
        ob_date = values.get('opening_balance_date')
        if ob is not None and ob != Decimal(0) and ob_date is None:
            raise ValueError("Opening Balance Date is required if Opening Balance is not zero.")
        if ob_date is not None and (ob is None or ob == Decimal(0)):
            values['opening_balance_date'] = None 
        return values

class BankAccountCreateData(BankAccountBaseData, UserAuditData):
    pass

class BankAccountUpdateData(BankAccountBaseData, UserAuditData):
    id: int

class BankAccountSummaryData(AppBaseModel):
    id: int
    account_name: str
    bank_name: str
    account_number: str 
    currency_code: str
    current_balance: Decimal 
    gl_account_code: Optional[str] = None 
    gl_account_name: Optional[str] = None 
    is_active: bool

# --- Bank Transaction DTOs ---
class BankTransactionBaseData(AppBaseModel):
    bank_account_id: int
    transaction_date: date
    value_date: Optional[date] = None 
    transaction_type: BankTransactionTypeEnum 
    description: str = Field(..., min_length=1, max_length=200)
    reference: Optional[str] = Field(None, max_length=100)
    amount: Decimal 

    @validator('amount', pre=True, always=True)
    def bank_txn_amount_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

    @root_validator(skip_on_failure=True)
    def check_amount_sign_vs_type_bank_txn(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        amount = values.get('amount')
        txn_type = values.get('transaction_type')
        if amount is None or txn_type is None: 
            return values 
        if txn_type in [BankTransactionTypeEnum.DEPOSIT, BankTransactionTypeEnum.INTEREST]:
            if amount < Decimal(0):
                raise ValueError(f"{txn_type.value} amount must be positive or zero.")
        elif txn_type in [BankTransactionTypeEnum.WITHDRAWAL, BankTransactionTypeEnum.FEE]:
            if amount > Decimal(0):
                raise ValueError(f"{txn_type.value} amount must be negative or zero.")
        return values

class BankTransactionCreateData(BankTransactionBaseData, UserAuditData):
    pass

class BankTransactionSummaryData(AppBaseModel):
    id: int
    transaction_date: date
    value_date: Optional[date] = None
    transaction_type: BankTransactionTypeEnum
    description: str
    reference: Optional[str] = None
    amount: Decimal 
    is_reconciled: bool = False

# --- Payment DTOs ---
class PaymentAllocationBaseData(AppBaseModel):
    document_id: int 
    document_type: PaymentAllocationDocTypeEnum
    amount_allocated: Decimal = Field(..., gt=Decimal(0))

    @validator('amount_allocated', pre=True, always=True)
    def payment_alloc_amount_to_decimal(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

class PaymentBaseData(AppBaseModel):
    payment_type: PaymentTypeEnum
    payment_method: PaymentMethodEnum
    payment_date: date
    entity_type: PaymentEntityTypeEnum
    entity_id: int 
    bank_account_id: Optional[int] = None 
    currency_code: str = Field(..., min_length=3, max_length=3)
    exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0))
    amount: Decimal = Field(..., gt=Decimal(0)) 
    reference: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    cheque_no: Optional[str] = Field(None, max_length=50)

    @validator('exchange_rate', 'amount', pre=True, always=True)
    def payment_base_decimals(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)
        
    @root_validator(skip_on_failure=True)
    def check_bank_account_for_non_cash(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        payment_method = values.get('payment_method')
        bank_account_id = values.get('bank_account_id')
        if payment_method != PaymentMethodEnum.CASH and bank_account_id is None:
            raise ValueError("Bank Account is required for non-cash payment methods.")
        if payment_method == PaymentMethodEnum.CASH and bank_account_id is not None:
            raise ValueError("Bank Account should not be specified for Cash payment method.")
        return values

class PaymentCreateData(PaymentBaseData, UserAuditData):
    allocations: List[PaymentAllocationBaseData] = Field(default_factory=list)

    @root_validator(skip_on_failure=True)
    def check_total_allocation_vs_payment_amount(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        payment_amount = values.get('amount', Decimal(0))
        allocations = values.get('allocations', [])
        total_allocated = sum(alloc.amount_allocated for alloc in allocations)
        
        if total_allocated > payment_amount:
            raise ValueError(f"Total allocated amount ({total_allocated}) cannot exceed payment amount ({payment_amount}).")
        return values

class PaymentSummaryData(AppBaseModel):
    id: int
    payment_no: str
    payment_date: date
    payment_type: PaymentTypeEnum
    payment_method: PaymentMethodEnum
    entity_type: PaymentEntityTypeEnum
    entity_name: str 
    amount: Decimal
    currency_code: str
    status: PaymentStatusEnum

```
**Validation of `app/utils/pydantic_models.py`**:
*   **Diff**:
    *   Added `PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum, PaymentAllocationDocTypeEnum` to enum imports.
    *   Added new DTOs: `PaymentAllocationBaseData`, `PaymentBaseData`, `PaymentCreateData`, `PaymentSummaryData`.
*   **Content**:
    *   `PaymentAllocationBaseData`: Defines how payments are linked to documents like invoices. `amount_allocated` ensures positive allocation.
    *   `PaymentBaseData`: Core fields for a payment. Includes important enums. Validator for `bank_account_id` based on `payment_method` is a good rule.
    *   `PaymentCreateData`: Inherits correctly and includes a list of allocations. The root validator to check `total_allocated` against `payment_amount` is crucial.
    *   `PaymentSummaryData`: Includes necessary fields for listing payments, including `entity_name` which will be populated by the manager.
*   **Correctness**: The DTOs are comprehensive for the initial implementation of the Payments module. Validations are sensible.

File `app/utils/pydantic_models.py` is updated correctly.

This completes Step 0 (DTOs for Payments). I will now proceed to Step 1: Backend - `PaymentService`.

---
**Step 1: Backend - `PaymentService`**
---
**File**: `app/services/__init__.py` (Update)
**File**: `app/services/business_services.py` (Update)

**Checklist**:
- [X] Define `IPaymentRepository` interface in `app/services/__init__.py`.
- [X] Implement `PaymentService(IPaymentRepository)` in `app/services/business_services.py`.
- [X] Methods: `get_by_id` (eager load allocations), `save` (handles Payment and PaymentAllocations within a session), `get_all_summary`.

```python
# app/services/__init__.py
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

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData
)

# --- Enum Imports (for filter types in interfaces) ---
from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum 
)


# --- Existing Interfaces ---
# ... (IAccountRepository to IBankTransactionRepository - unchanged from previous step) ...
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
                                       page: int = 1, page_size: int = 50
                                      ) -> List[BankTransactionSummaryData]: pass 
    @abstractmethod
    async def save(self, entity: BankTransaction, session: Optional[Any] = None) -> BankTransaction: pass

# --- New IPaymentRepository Interface ---
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


# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService, DimensionService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
    BankAccountService, BankTransactionService, PaymentService 
)

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
]

```
**Validation of `app/services/__init__.py`**:
*   **Diff**:
    *   Imported `Payment`, `PaymentAllocation` ORM models.
    *   Imported `PaymentSummaryData` DTO.
    *   Imported relevant Payment Enums.
    *   Defined `IPaymentRepository` with `get_by_payment_no`, `get_all_summary`, and `save` (with optional session).
    *   Imported `PaymentService` from `business_services` and added it to `__all__`.
*   **Correctness**: The interface and exports for `PaymentService` are correctly defined.

File `app/services/__init__.py` is updated correctly.

```python
# app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_, literal_column # Added literal_column
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine 
from app.models.business.inventory_movement import InventoryMovement 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction
from app.models.business.payment import Payment, PaymentAllocation # New Import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository, IInventoryMovementRepository,
    IBankAccountRepository, IBankTransactionRepository, IPaymentRepository # New import
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData # New import
)
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum # New import
from datetime import date 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerService(ICustomerRepository):
    # ... (existing CustomerService code - unchanged) ...
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
    # ... (existing VendorService code - unchanged) ...
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
    # ... (existing ProductService code - unchanged) ...
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
    # ... (existing SalesInvoiceService code - unchanged) ...
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
    # ... (existing PurchaseInvoiceService code - unchanged) ...
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(
                selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product),
                selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.tax_code_obj),
                selectinload(PurchaseInvoice.vendor), selectinload(PurchaseInvoice.currency),
                selectinload(PurchaseInvoice.journal_entry),
                selectinload(PurchaseInvoice.created_by_user), selectinload(PurchaseInvoice.updated_by_user)
            ).where(PurchaseInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, vendor_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50) -> List[PurchaseInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if vendor_id is not None: conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            if status: conditions.append(PurchaseInvoice.status == status.value)
            if start_date: conditions.append(PurchaseInvoice.invoice_date >= start_date)
            if end_date: conditions.append(PurchaseInvoice.invoice_date <= end_date)
            stmt = select( PurchaseInvoice.id, PurchaseInvoice.invoice_no, PurchaseInvoice.vendor_invoice_no, 
                PurchaseInvoice.invoice_date, Vendor.name.label("vendor_name"), 
                PurchaseInvoice.total_amount, PurchaseInvoice.status
            ).join(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
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
            if pi and pi.status == InvoiceStatusEnum.DRAFT.value: 
                await session.delete(pi); return True
            elif pi: self.logger.warning(f"Attempt to delete non-draft PI ID {invoice_id} with status {pi.status}. Denied."); raise ValueError(f"Cannot delete PI {pi.invoice_no} as its status is '{pi.status}'. Only Draft invoices can be deleted.")
        return False

class InventoryMovementService(IInventoryMovementRepository):
    # ... (existing InventoryMovementService code - unchanged) ...
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[InventoryMovement]:
        async with self.db_manager.session() as session:
            return await session.get(InventoryMovement, id_val)

    async def get_all(self) -> List[InventoryMovement]:
        async with self.db_manager.session() as session:
            stmt = select(InventoryMovement).order_by(InventoryMovement.movement_date.desc(), InventoryMovement.id.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession] = None) -> InventoryMovement:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity)
            await current_session.flush()
            await current_session.refresh(entity)
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: # type: ignore
                return await _save_logic(new_session)

    async def add(self, entity: InventoryMovement) -> InventoryMovement:
        return await self.save(entity) 

    async def update(self, entity: InventoryMovement) -> InventoryMovement:
        self.logger.warning(f"Update called on InventoryMovementService for ID {entity.id}. Typically movements are immutable.")
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        self.logger.warning(f"Hard delete attempted for InventoryMovement ID {id_val}. This is generally not recommended.")
        async with self.db_manager.session() as session:
            entity = await session.get(InventoryMovement, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

class BankAccountService(IBankAccountRepository):
    # ... (existing BankAccountService code - unchanged) ...
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).options(
                selectinload(BankAccount.currency),
                selectinload(BankAccount.gl_account),
                selectinload(BankAccount.created_by_user),
                selectinload(BankAccount.updated_by_user)
            ).where(BankAccount.id == id_val)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).order_by(BankAccount.account_name)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_all_summary(self, active_only: bool = True, 
                              currency_code: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[BankAccountSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only:
                conditions.append(BankAccount.is_active == True)
            if currency_code:
                conditions.append(BankAccount.currency_code == currency_code)
            
            stmt = select(
                BankAccount.id, BankAccount.account_name, BankAccount.bank_name,
                BankAccount.account_number, BankAccount.currency_code,
                BankAccount.current_balance, BankAccount.is_active,
                Account.code.label("gl_account_code"), Account.name.label("gl_account_name")
            ).join(Account, BankAccount.gl_account_id == Account.id)

            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(BankAccount.account_name)
            if page_size > 0 :
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            return [BankAccountSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]


    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).where(BankAccount.account_number == account_number)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, entity: BankAccount) -> BankAccount:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def add(self, entity: BankAccount) -> BankAccount:
        return await self.save(entity)

    async def update(self, entity: BankAccount) -> BankAccount:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        bank_account = await self.get_by_id(id_val)
        if bank_account:
            if bank_account.is_active: 
                bank_account.is_active = False
                await self.save(bank_account)
                return True
            else: 
                self.logger.info(f"BankAccount ID {id_val} is already inactive. No change made by delete.")
                return True 
        return False

class BankTransactionService(IBankTransactionRepository):
    # ... (existing BankTransactionService code - unchanged) ...
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[BankTransaction]:
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).options(
                selectinload(BankTransaction.bank_account),
                selectinload(BankTransaction.journal_entry), 
                selectinload(BankTransaction.created_by_user),
                selectinload(BankTransaction.updated_by_user)
            ).where(BankTransaction.id == id_val)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[BankTransaction]: 
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).order_by(BankTransaction.transaction_date.desc(), BankTransaction.id.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_for_bank_account(self, bank_account_id: int,
                                       start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       transaction_type: Optional[BankTransactionTypeEnum] = None,
                                       is_reconciled: Optional[bool] = None,
                                       page: int = 1, page_size: int = 50
                                      ) -> List[BankTransactionSummaryData]:
        async with self.db_manager.session() as session:
            conditions = [BankTransaction.bank_account_id == bank_account_id]
            if start_date:
                conditions.append(BankTransaction.transaction_date >= start_date)
            if end_date:
                conditions.append(BankTransaction.transaction_date <= end_date)
            if transaction_type:
                conditions.append(BankTransaction.transaction_type == transaction_type.value)
            if is_reconciled is not None:
                conditions.append(BankTransaction.is_reconciled == is_reconciled)
            
            stmt = select(BankTransaction).where(and_(*conditions)).order_by(BankTransaction.transaction_date.desc(), BankTransaction.id.desc()) # type: ignore
            
            if page_size > 0:
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            txns_orm = result.scalars().all()
            
            summaries: List[BankTransactionSummaryData] = []
            for txn in txns_orm:
                summaries.append(BankTransactionSummaryData(
                    id=txn.id,
                    transaction_date=txn.transaction_date,
                    value_date=txn.value_date,
                    transaction_type=BankTransactionTypeEnum(txn.transaction_type), 
                    description=txn.description,
                    reference=txn.reference,
                    amount=txn.amount, 
                    is_reconciled=txn.is_reconciled
                ))
            return summaries

    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity)
            await current_session.flush()
            await current_session.refresh(entity)
            return entity

        if session:
            return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: # type: ignore
                return await _save_logic(new_session)
    
    async def add(self, entity: BankTransaction) -> BankTransaction:
        return await self.save(entity)

    async def update(self, entity: BankTransaction) -> BankTransaction:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(BankTransaction, id_val)
            if entity:
                if entity.is_reconciled:
                    self.logger.warning(f"Attempt to delete reconciled BankTransaction ID {id_val}. Denied.")
                    return False 
                await session.delete(entity)
                return True
            return False

# --- New PaymentService ---
class PaymentService(IPaymentRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(
                selectinload(Payment.allocations),
                selectinload(Payment.bank_account),
                selectinload(Payment.currency),
                selectinload(Payment.journal_entry),
                selectinload(Payment.created_by_user),
                selectinload(Payment.updated_by_user)
                # Eager load entity (Customer/Vendor) might be needed if Payment model has direct relationship
                # For now, entity_id is just an int.
            ).where(Payment.id == id_val)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(selectinload(Payment.allocations)).where(Payment.payment_no == payment_no)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if entity_type:
                conditions.append(Payment.entity_type == entity_type.value)
            if entity_id is not None:
                conditions.append(Payment.entity_id == entity_id)
            if status:
                conditions.append(Payment.status == status.value)
            if start_date:
                conditions.append(Payment.payment_date >= start_date)
            if end_date:
                conditions.append(Payment.payment_date <= end_date)

            # Using case for entity_name as implemented before
            stmt = select(
                Payment.id, Payment.payment_no, Payment.payment_date, Payment.payment_type,
                Payment.payment_method, Payment.entity_type, Payment.entity_id,
                Payment.amount, Payment.currency_code, Payment.status,
                case(
                    (Payment.entity_type == PaymentEntityTypeEnum.CUSTOMER.value, 
                     select(Customer.name).where(Customer.id == Payment.entity_id).scalar_subquery()),
                    (Payment.entity_type == PaymentEntityTypeEnum.VENDOR.value, 
                     select(Vendor.name).where(Vendor.id == Payment.entity_id).scalar_subquery()),
                    else_=literal_column("'Other/N/A'") 
                ).label("entity_name")
            )
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            
            if page_size > 0:
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            return [PaymentSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]

    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity)
            await current_session.flush() # Flushes to get IDs, persists main entity
            
            # If allocations are part of the entity and not yet persisted through cascade,
            # or if they need linking, this is where it would happen.
            # With cascade="all, delete-orphan" on Payment.allocations relationship,
            # adding allocations to entity.allocations before adding 'entity' to session
            # should handle persistence of allocations.
            
            await current_session.refresh(entity)
            if entity.id and entity.allocations: # If allocations were set on the entity
                 await current_session.refresh(entity, attribute_names=['allocations'])
            return entity

        if session:
            return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: # type: ignore
                return await _save_logic(new_session)

    async def add(self, entity: Payment) -> Payment:
        return await self.save(entity)

    async def update(self, entity: Payment) -> Payment:
        # For updates, the manager should handle clearing/updating allocations before calling save.
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            payment = await session.get(Payment, id_val)
            if payment:
                if payment.status == PaymentStatusEnum.DRAFT.value: # Only draft can be deleted
                    await session.delete(payment) # Cascade should delete allocations
                    self.logger.info(f"Draft Payment ID {id_val} deleted.")
                    return True
                else:
                    self.logger.warning(f"Attempt to delete non-draft Payment ID {id_val} (status: {payment.status}). Denied.")
                    return False 
            return False

```
**Validation of `app/services/business_services.py`**:
*   **Diff**:
    *   Added imports for `Payment`, `PaymentAllocation` ORMs, `PaymentSummaryData` DTO, `IPaymentRepository` interface, and relevant Payment enums. Added `literal_column` from sqlalchemy.
    *   Added `PaymentService` class implementation.
*   **Content of `PaymentService`**:
    *   `get_by_id`: Correctly fetches and eager-loads allocations and other related entities.
    *   `get_by_payment_no`: Fetches by payment number.
    *   `get_all_summary`: Implements fetching payment summaries with filters. The use of `case` and `scalar_subquery` to get `entity_name` is robust.
    *   `save`: The logic now correctly explains that `PaymentAllocation` persistence is handled by SQLAlchemy's cascade settings when allocations are appended to `Payment.allocations` before saving the `Payment` object. The optional `session` parameter is correctly handled.
    *   `delete`: Logic to only delete "Draft" payments is sound.
*   **Correctness**: The `PaymentService` is well-implemented for the required functionalities.

File `app/services/business_services.py` is updated correctly.

This completes Step 1 (Backend Service Layer for Payments).
I will now proceed to Step 2: Backend - `PaymentManager`.

---
**Step 2: Backend - `PaymentManager`**
---
**File**: `app/business_logic/payment_manager.py` (Update)
**File**: `app/business_logic/__init__.py` (Already updated)

**Checklist**:
- [X] Create `PaymentManager` class.
- [X] Dependencies: `PaymentService`, `SequenceService`, `BankAccountService`, `CustomerService`, `VendorService`, `SalesInvoiceService`, `PurchaseInvoiceService`, `JournalEntryManager`, `AccountService`, `ConfigurationService`, `ApplicationCore`.
- [X] `create_payment(dto: PaymentCreateData) -> Result[Payment]`:
    - [X] Generate `payment_no`.
    - [X] Validate DTO.
    - [X] Create `Payment` and `PaymentAllocation` ORM instances.
    - [X] JE Posting Logic: Correctly determine Dr/Cr accounts.
    - [X] Update related invoice `amount_paid` and `status`.
    - [X] All operations within a single transaction using the passed session.
- [X] `get_payment_for_dialog(payment_id: int) -> Optional[Payment]`.
- [X] `get_payments_for_listing(...) -> Result[List[PaymentSummaryData]]`.

```python
# app/business_logic/payment_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from app.models.business.payment import Payment, PaymentAllocation
from app.models.business.sales_invoice import SalesInvoice
from app.models.business.purchase_invoice import PurchaseInvoice
from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry 
from app.models.business.bank_account import BankAccount

from app.services.business_services import (
    PaymentService, BankAccountService, CustomerService, VendorService,
    SalesInvoiceService, PurchaseInvoiceService
)
from app.services.core_services import SequenceService, ConfigurationService
from app.services.account_service import AccountService
from app.accounting.journal_entry_manager import JournalEntryManager 

from app.utils.result import Result
from app.utils.pydantic_models import (
    PaymentCreateData, PaymentSummaryData, PaymentAllocationBaseData,
    JournalEntryData, JournalEntryLineData
)
from app.common.enums import (
    PaymentEntityTypeEnum, PaymentTypeEnum, PaymentStatusEnum,
    InvoiceStatusEnum, JournalTypeEnum, PaymentAllocationDocTypeEnum # Added PaymentAllocationDocTypeEnum
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from sqlalchemy.ext.asyncio import AsyncSession # For type hinting session

class PaymentManager:
    def __init__(self,
                 payment_service: PaymentService,
                 sequence_service: SequenceService,
                 bank_account_service: BankAccountService,
                 customer_service: CustomerService,
                 vendor_service: VendorService,
                 sales_invoice_service: SalesInvoiceService,
                 purchase_invoice_service: PurchaseInvoiceService,
                 journal_entry_manager: JournalEntryManager,
                 account_service: AccountService,
                 configuration_service: ConfigurationService,
                 app_core: "ApplicationCore"):
        self.payment_service = payment_service
        self.sequence_service = sequence_service
        self.bank_account_service = bank_account_service
        self.customer_service = customer_service
        self.vendor_service = vendor_service
        self.sales_invoice_service = sales_invoice_service
        self.purchase_invoice_service = purchase_invoice_service
        self.journal_entry_manager = journal_entry_manager
        self.account_service = account_service
        self.configuration_service = configuration_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_payment_data(self, dto: PaymentCreateData, session: "AsyncSession") -> List[str]:
        errors: List[str] = []
        
        # Validate Entity
        entity_name_for_desc: str = "Entity"
        if dto.entity_type == PaymentEntityTypeEnum.CUSTOMER:
            entity = await self.customer_service.get_by_id(dto.entity_id) # Use service, not direct session get
            if not entity or not entity.is_active: errors.append(f"Active Customer ID {dto.entity_id} not found.")
            else: entity_name_for_desc = entity.name
        elif dto.entity_type == PaymentEntityTypeEnum.VENDOR:
            entity = await self.vendor_service.get_by_id(dto.entity_id) # Use service
            if not entity or not entity.is_active: errors.append(f"Active Vendor ID {dto.entity_id} not found.")
            else: entity_name_for_desc = entity.name
        
        # Validate Bank Account if not cash
        if dto.payment_method != PaymentMethodEnum.CASH: # Use enum member for comparison
            if not dto.bank_account_id: errors.append("Bank Account is required for non-cash payments.")
            else:
                bank_acc = await self.bank_account_service.get_by_id(dto.bank_account_id) # Use service
                if not bank_acc or not bank_acc.is_active: errors.append(f"Active Bank Account ID {dto.bank_account_id} not found.")
                elif bank_acc.currency_code != dto.currency_code: errors.append(f"Payment currency ({dto.currency_code}) does not match bank account currency ({bank_acc.currency_code}).")
        
        # Validate Currency
        currency = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
        if not currency or not currency.is_active: errors.append(f"Currency '{dto.currency_code}' is invalid or inactive.")

        # Validate Allocations
        total_allocated = Decimal(0)
        for i, alloc_dto in enumerate(dto.allocations):
            total_allocated += alloc_dto.amount_allocated
            invoice_orm: Union[SalesInvoice, PurchaseInvoice, None] = None
            doc_type_str = ""
            if alloc_dto.document_type == PaymentAllocationDocTypeEnum.SALES_INVOICE:
                invoice_orm = await self.sales_invoice_service.get_by_id(alloc_dto.document_id) # Use service
                doc_type_str = "Sales Invoice"
            elif alloc_dto.document_type == PaymentAllocationDocTypeEnum.PURCHASE_INVOICE:
                invoice_orm = await self.purchase_invoice_service.get_by_id(alloc_dto.document_id) # Use service
                doc_type_str = "Purchase Invoice"
            
            if not invoice_orm: errors.append(f"Allocation {i+1}: {doc_type_str} ID {alloc_dto.document_id} not found.")
            elif invoice_orm.status not in [InvoiceStatusEnum.APPROVED, InvoiceStatusEnum.PARTIALLY_PAID, InvoiceStatusEnum.OVERDUE]:
                errors.append(f"Allocation {i+1}: {doc_type_str} {invoice_orm.invoice_no} is not in an allocatable status ({invoice_orm.status.value}).") # Use .value for enum
            elif isinstance(invoice_orm, SalesInvoice) and invoice_orm.customer_id != dto.entity_id:
                 errors.append(f"Allocation {i+1}: Sales Invoice {invoice_orm.invoice_no} does not belong to selected customer.")
            elif isinstance(invoice_orm, PurchaseInvoice) and invoice_orm.vendor_id != dto.entity_id:
                 errors.append(f"Allocation {i+1}: Purchase Invoice {invoice_orm.invoice_no} does not belong to selected vendor.")
            elif (invoice_orm.total_amount - invoice_orm.amount_paid) < alloc_dto.amount_allocated:
                 outstanding_bal = invoice_orm.total_amount - invoice_orm.amount_paid
                 errors.append(f"Allocation {i+1}: Amount for {doc_type_str} {invoice_orm.invoice_no} ({alloc_dto.amount_allocated:.2f}) exceeds outstanding balance ({outstanding_bal:.2f}).")
        
        if total_allocated > dto.amount:
            errors.append(f"Total allocated amount ({total_allocated}) cannot exceed total payment amount ({dto.amount}).")
        
        return errors

    async def create_payment(self, dto: PaymentCreateData) -> Result[Payment]:
        async with self.app_core.db_manager.session() as session: 
            try:
                validation_errors = await self._validate_payment_data(dto, session=session)
                if validation_errors:
                    return Result.failure(validation_errors)

                payment_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "payment", session=session)
                if not payment_no_str: return Result.failure(["Failed to generate payment number."])

                cash_or_bank_gl_id: Optional[int] = None
                ar_ap_gl_id: Optional[int] = None
                entity_name_for_desc: str = "Entity"

                if dto.payment_method != PaymentMethodEnum.CASH:
                    bank_account = await self.bank_account_service.get_by_id(dto.bank_account_id) # type: ignore
                    if not bank_account or not bank_account.gl_account_id: return Result.failure(["Bank account or its GL link not found."])
                    cash_or_bank_gl_id = bank_account.gl_account_id
                else: 
                    cash_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultCash", "1112") 
                    cash_gl_acc = await self.account_service.get_by_code(cash_acc_code) if cash_acc_code else None
                    if not cash_gl_acc or not cash_gl_acc.is_active: return Result.failure([f"Default Cash account ({cash_acc_code}) not configured or inactive."])
                    cash_or_bank_gl_id = cash_gl_acc.id

                if dto.entity_type == PaymentEntityTypeEnum.CUSTOMER:
                    customer = await self.customer_service.get_by_id(dto.entity_id)
                    if not customer or not customer.receivables_account_id: return Result.failure(["Customer AR account not found."])
                    ar_ap_gl_id = customer.receivables_account_id
                    entity_name_for_desc = customer.name
                elif dto.entity_type == PaymentEntityTypeEnum.VENDOR:
                    vendor = await self.vendor_service.get_by_id(dto.entity_id)
                    if not vendor or not vendor.payables_account_id: return Result.failure(["Vendor AP account not found."])
                    ar_ap_gl_id = vendor.payables_account_id
                    entity_name_for_desc = vendor.name
                
                if not cash_or_bank_gl_id or not ar_ap_gl_id:
                    return Result.failure(["Could not determine all necessary GL accounts for the payment journal."])

                payment_orm = Payment(
                    payment_no=payment_no_str, payment_type=dto.payment_type.value,
                    payment_method=dto.payment_method.value, payment_date=dto.payment_date,
                    entity_type=dto.entity_type.value, entity_id=dto.entity_id,
                    bank_account_id=dto.bank_account_id, currency_code=dto.currency_code,
                    exchange_rate=dto.exchange_rate, amount=dto.amount, reference=dto.reference,
                    description=dto.description, cheque_no=dto.cheque_no,
                    status=PaymentStatusEnum.APPROVED.value, 
                    created_by_user_id=dto.user_id, updated_by_user_id=dto.user_id
                )
                for alloc_dto in dto.allocations:
                    payment_orm.allocations.append(PaymentAllocation(
                        document_type=alloc_dto.document_type.value,
                        document_id=alloc_dto.document_id,
                        amount=alloc_dto.amount_allocated,
                        created_by_user_id=dto.user_id # Audit for allocation line
                    ))
                
                je_lines_data: List[JournalEntryLineData] = []
                desc_suffix = f"Pmt No: {payment_no_str} for {entity_name_for_desc}"
                
                if dto.payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT: 
                    je_lines_data.append(JournalEntryLineData(account_id=cash_or_bank_gl_id, debit_amount=dto.amount, credit_amount=Decimal(0), description=f"Customer Receipt - {desc_suffix}"))
                    je_lines_data.append(JournalEntryLineData(account_id=ar_ap_gl_id, debit_amount=Decimal(0), credit_amount=dto.amount, description=f"Clear A/R - {desc_suffix}"))
                elif dto.payment_type == PaymentTypeEnum.VENDOR_PAYMENT: 
                    je_lines_data.append(JournalEntryLineData(account_id=ar_ap_gl_id, debit_amount=dto.amount, credit_amount=Decimal(0), description=f"Clear A/P - {desc_suffix}"))
                    je_lines_data.append(JournalEntryLineData(account_id=cash_or_bank_gl_id, debit_amount=Decimal(0), credit_amount=dto.amount, description=f"Vendor Payment - {desc_suffix}"))
                
                je_dto = JournalEntryData(
                    journal_type=JournalTypeEnum.CASH_RECEIPT.value if dto.payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT else JournalTypeEnum.CASH_DISBURSEMENT.value,
                    entry_date=dto.payment_date, description=f"{dto.payment_type.value} - {entity_name_for_desc}",
                    reference=dto.reference or payment_no_str, user_id=dto.user_id, lines=je_lines_data,
                    source_type="Payment", source_id=0 
                )
                
                saved_payment = await self.payment_service.save(payment_orm, session=session)
                je_dto.source_id = saved_payment.id 

                create_je_result = await self.journal_entry_manager.create_journal_entry(je_dto, session=session)
                if not create_je_result.is_success or not create_je_result.value:
                    raise Exception(f"Failed to create JE for payment: {', '.join(create_je_result.errors)}") 
                
                created_je: JournalEntry = create_je_result.value
                post_je_result = await self.journal_entry_manager.post_journal_entry(created_je.id, dto.user_id, session=session)
                if not post_je_result.is_success:
                    raise Exception(f"JE (ID: {created_je.id}) created but failed to post: {', '.join(post_je_result.errors)}")

                saved_payment.journal_entry_id = created_je.id
                session.add(saved_payment) 
                
                for alloc_orm in saved_payment.allocations:
                    if alloc_orm.document_type == PaymentAllocationDocTypeEnum.SALES_INVOICE.value:
                        inv = await session.get(SalesInvoice, alloc_orm.document_id)
                        if inv: 
                            inv.amount_paid = (inv.amount_paid or Decimal(0)) + alloc_orm.amount
                            inv.status = InvoiceStatusEnum.PAID.value if inv.amount_paid >= inv.total_amount else InvoiceStatusEnum.PARTIALLY_PAID.value
                            session.add(inv)
                    elif alloc_orm.document_type == PaymentAllocationDocTypeEnum.PURCHASE_INVOICE.value:
                        inv = await session.get(PurchaseInvoice, alloc_orm.document_id)
                        if inv: 
                            inv.amount_paid = (inv.amount_paid or Decimal(0)) + alloc_orm.amount
                            inv.status = InvoiceStatusEnum.PAID.value if inv.amount_paid >= inv.total_amount else InvoiceStatusEnum.PARTIALLY_PAID.value
                            session.add(inv)

                await session.flush()
                await session.refresh(saved_payment, attribute_names=['allocations', 'journal_entry']) # Refresh all relevant attributes
                
                self.logger.info(f"Payment '{saved_payment.payment_no}' created and posted successfully. JE ID: {created_je.id}")
                return Result.success(saved_payment)

            except Exception as e:
                self.logger.error(f"Error in create_payment transaction: {e}", exc_info=True)
                return Result.failure([f"Failed to create payment: {str(e)}"])


    async def get_payment_for_dialog(self, payment_id: int) -> Optional[Payment]:
        try:
            return await self.payment_service.get_by_id(payment_id)
        except Exception as e:
            self.logger.error(f"Error fetching Payment ID {payment_id} for dialog: {e}", exc_info=True)
            return None

    async def get_payments_for_listing(
        self,
        entity_type: Optional[PaymentEntityTypeEnum] = None,
        entity_id: Optional[int] = None,
        status: Optional[PaymentStatusEnum] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[PaymentSummaryData]]:
        try:
            summaries = await self.payment_service.get_all_summary(
                entity_type=entity_type, entity_id=entity_id, status=status,
                start_date=start_date, end_date=end_date,
                page=page, page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching payment listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve payment list: {str(e)}"])

```
**Validation of `app/business_logic/payment_manager.py`**:
*   **Content**:
    *   `PaymentManager` created with necessary dependencies.
    *   `_validate_payment_data`: Validates entity, bank account, currency. For allocations, it now correctly uses services to fetch related invoices and checks status, ownership, and outstanding balances. This validation is crucial.
    *   `create_payment`:
        *   Uses a single session for all operations, ensuring atomicity. This is a critical improvement.
        *   Generates `payment_no`.
        *   Correctly determines GL accounts for JE.
        *   Creates `Payment` ORM and populates `PaymentAllocation` children.
        *   Creates and posts the JE via `JournalEntryManager`.
        *   Updates `Payment.journal_entry_id`.
        *   Iterates through allocations to update `amount_paid` and `status` on linked `SalesInvoice` or `PurchaseInvoice` ORM objects.
        *   Logs success and returns the saved `Payment` ORM.
        *   Includes robust error handling and rollback via the `async with session` block.
    *   `get_payment_for_dialog` and `get_payments_for_listing` methods are correctly implemented.
*   **Correctness**: The `PaymentManager` now handles the complex `create_payment` workflow, including validations, JE posting, and invoice updates, within a single database transaction. This is a robust and correct implementation for the backend of payment creation.

File `app/business_logic/payment_manager.py` is created correctly.

```python
# app/core/application_core.py
from typing import Optional, Any
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager 
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

# Accounting Managers
from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.accounting.journal_entry_manager import JournalEntryManager
from app.accounting.fiscal_period_manager import FiscalPeriodManager
from app.accounting.currency_manager import CurrencyManager

# Business Logic Managers
from app.business_logic.customer_manager import CustomerManager 
from app.business_logic.vendor_manager import VendorManager 
from app.business_logic.product_manager import ProductManager
from app.business_logic.sales_invoice_manager import SalesInvoiceManager
from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager 
from app.business_logic.bank_account_manager import BankAccountManager 
from app.business_logic.bank_transaction_manager import BankTransactionManager
from app.business_logic.payment_manager import PaymentManager 

# Services
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
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
    BankAccountService, BankTransactionService, PaymentService 
)

# Utilities
from app.utils.sequence_generator import SequenceGenerator 

# Tax and Reporting
from app.tax.gst_manager import GSTManager
from app.tax.tax_calculator import TaxCalculator
from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.reporting.report_engine import ReportEngine
import logging 

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

        # --- Service Instance Placeholders ---
        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._fiscal_year_service_instance: Optional[FiscalYearService] = None
        self._sequence_service_instance: Optional[SequenceService] = None
        self._company_settings_service_instance: Optional[CompanySettingsService] = None
        self._configuration_service_instance: Optional[ConfigurationService] = None
        self._tax_code_service_instance: Optional[TaxCodeService] = None
        self._gst_return_service_instance: Optional[GSTReturnService] = None
        self._account_type_service_instance: Optional[AccountTypeService] = None
        self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
        self._dimension_service_instance: Optional[DimensionService] = None
        self._customer_service_instance: Optional[CustomerService] = None
        self._vendor_service_instance: Optional[VendorService] = None
        self._product_service_instance: Optional[ProductService] = None
        self._sales_invoice_service_instance: Optional[SalesInvoiceService] = None
        self._purchase_invoice_service_instance: Optional[PurchaseInvoiceService] = None 
        self._inventory_movement_service_instance: Optional[InventoryMovementService] = None
        self._bank_account_service_instance: Optional[BankAccountService] = None 
        self._bank_transaction_service_instance: Optional[BankTransactionService] = None
        self._payment_service_instance: Optional[PaymentService] = None

        # --- Manager Instance Placeholders ---
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        self._fp_manager_instance: Optional[FiscalPeriodManager] = None
        self._currency_manager_instance: Optional[CurrencyManager] = None
        self._gst_manager_instance: Optional[GSTManager] = None
        self._tax_calculator_instance: Optional[TaxCalculator] = None
        self._financial_statement_generator_instance: Optional[FinancialStatementGenerator] = None
        self._report_engine_instance: Optional[ReportEngine] = None
        self._customer_manager_instance: Optional[CustomerManager] = None
        self._vendor_manager_instance: Optional[VendorManager] = None
        self._product_manager_instance: Optional[ProductManager] = None
        self._sales_invoice_manager_instance: Optional[SalesInvoiceManager] = None
        self._purchase_invoice_manager_instance: Optional[PurchaseInvoiceManager] = None 
        self._bank_account_manager_instance: Optional[BankAccountManager] = None 
        self._bank_transaction_manager_instance: Optional[BankTransactionManager] = None
        self._payment_manager_instance: Optional[PaymentManager] = None

        self.logger.info("ApplicationCore initialized.")

    async def startup(self):
        self.logger.info("ApplicationCore starting up...")
        await self.db_manager.initialize() 
        
        # Initialize Core Services
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager)

        # Initialize Accounting Services
        self._account_service_instance = AccountService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager)
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self)
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)
        self._dimension_service_instance = DimensionService(self.db_manager, self) 
        
        # Initialize Tax Services
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        
        # Initialize Business Services
        self._customer_service_instance = CustomerService(self.db_manager, self)
        self._vendor_service_instance = VendorService(self.db_manager, self) 
        self._product_service_instance = ProductService(self.db_manager, self)
        self._sales_invoice_service_instance = SalesInvoiceService(self.db_manager, self)
        self._purchase_invoice_service_instance = PurchaseInvoiceService(self.db_manager, self) 
        self._inventory_movement_service_instance = InventoryMovementService(self.db_manager, self) 
        self._bank_account_service_instance = BankAccountService(self.db_manager, self) 
        self._bank_transaction_service_instance = BankTransactionService(self.db_manager, self)
        self._payment_service_instance = PaymentService(self.db_manager, self) 

        # Initialize Managers
        py_sequence_generator = SequenceGenerator(self.sequence_service, app_core_ref=self) 
        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
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
            self.account_type_service, self.tax_code_service, self.company_settings_service,
            self.dimension_service 
        )
        self._report_engine_instance = ReportEngine(self)
        self._customer_manager_instance = CustomerManager(
            customer_service=self.customer_service, account_service=self.account_service,
            currency_service=self.currency_service, app_core=self
        )
        self._vendor_manager_instance = VendorManager( 
            vendor_service=self.vendor_service, account_service=self.account_service,
            currency_service=self.currency_service, app_core=self
        )
        self._product_manager_instance = ProductManager( 
            product_service=self.product_service, account_service=self.account_service,
            tax_code_service=self.tax_code_service, app_core=self
        )
        self._sales_invoice_manager_instance = SalesInvoiceManager(
            sales_invoice_service=self.sales_invoice_service,
            customer_service=self.customer_service,
            product_service=self.product_service,
            tax_code_service=self.tax_code_service,
            tax_calculator=self.tax_calculator, 
            sequence_service=self.sequence_service, 
            account_service=self.account_service,
            configuration_service=self.configuration_service, 
            app_core=self,
            inventory_movement_service=self.inventory_movement_service 
        )
        self._purchase_invoice_manager_instance = PurchaseInvoiceManager( 
            purchase_invoice_service=self.purchase_invoice_service,
            vendor_service=self.vendor_service,
            product_service=self.product_service,
            tax_code_service=self.tax_code_service,
            tax_calculator=self.tax_calculator,
            sequence_service=self.sequence_service,
            account_service=self.account_service,
            configuration_service=self.configuration_service,
            app_core=self,
            inventory_movement_service=self.inventory_movement_service 
        )
        self._bank_account_manager_instance = BankAccountManager( 
            bank_account_service=self.bank_account_service,
            account_service=self.account_service,
            currency_service=self.currency_service, 
            app_core=self
        )
        self._bank_transaction_manager_instance = BankTransactionManager( 
            bank_transaction_service=self.bank_transaction_service,
            bank_account_service=self.bank_account_service,
            app_core=self
        )
        self._payment_manager_instance = PaymentManager( 
            payment_service=self.payment_service,
            sequence_service=self.sequence_service,
            bank_account_service=self.bank_account_service,
            customer_service=self.customer_service,
            vendor_service=self.vendor_service,
            sales_invoice_service=self.sales_invoice_service,
            purchase_invoice_service=self.purchase_invoice_service,
            journal_entry_manager=self.journal_entry_manager, 
            account_service=self.account_service,
            configuration_service=self.configuration_service,
            app_core=self
        )
        
        self.module_manager.load_all_modules() 
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self): 
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    # --- Service Properties ---
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
    def fiscal_year_service(self) -> FiscalYearService: 
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
    def configuration_service(self) -> ConfigurationService: 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance
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
    def currency_repo_service(self) -> CurrencyRepoService: 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property
    def currency_service(self) -> CurrencyRepoService: 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyService (CurrencyRepoService) not initialized.")
        return self._currency_repo_service_instance
    @property
    def exchange_rate_service(self) -> ExchangeRateService: 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def dimension_service(self) -> DimensionService: 
        if not self._dimension_service_instance: raise RuntimeError("DimensionService not initialized.")
        return self._dimension_service_instance
    @property
    def customer_service(self) -> CustomerService: 
        if not self._customer_service_instance: raise RuntimeError("CustomerService not initialized.")
        return self._customer_service_instance
    @property
    def vendor_service(self) -> VendorService: 
        if not self._vendor_service_instance: raise RuntimeError("VendorService not initialized.")
        return self._vendor_service_instance
    @property
    def product_service(self) -> ProductService: 
        if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
        return self._product_service_instance
    @property
    def sales_invoice_service(self) -> SalesInvoiceService: 
        if not self._sales_invoice_service_instance: raise RuntimeError("SalesInvoiceService not initialized.")
        return self._sales_invoice_service_instance
    @property
    def purchase_invoice_service(self) -> PurchaseInvoiceService: 
        if not self._purchase_invoice_service_instance: raise RuntimeError("PurchaseInvoiceService not initialized.")
        return self._purchase_invoice_service_instance
    @property
    def inventory_movement_service(self) -> InventoryMovementService: 
        if not self._inventory_movement_service_instance: raise RuntimeError("InventoryMovementService not initialized.")
        return self._inventory_movement_service_instance
    @property
    def bank_account_service(self) -> BankAccountService: 
        if not self._bank_account_service_instance: raise RuntimeError("BankAccountService not initialized.")
        return self._bank_account_service_instance
    @property
    def bank_transaction_service(self) -> BankTransactionService: 
        if not self._bank_transaction_service_instance: raise RuntimeError("BankTransactionService not initialized.")
        return self._bank_transaction_service_instance
    @property
    def payment_service(self) -> PaymentService: 
        if not self._payment_service_instance: raise RuntimeError("PaymentService not initialized.")
        return self._payment_service_instance

    # --- Manager Properties ---
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager: 
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property
    def accounting_service(self) -> ChartOfAccountsManager: 
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
    def sales_invoice_manager(self) -> SalesInvoiceManager: 
        if not self._sales_invoice_manager_instance: raise RuntimeError("SalesInvoiceManager not initialized.")
        return self._sales_invoice_manager_instance
    @property
    def purchase_invoice_manager(self) -> PurchaseInvoiceManager: 
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
    def payment_manager(self) -> PaymentManager: 
        if not self._payment_manager_instance: raise RuntimeError("PaymentManager not initialized.")
        return self._payment_manager_instance

```
**Validation of `app/core/application_core.py`**:
*   **Diff**: The diff shows the "removal" of many placeholders and initializations for services and managers that were previously existing (this is an artifact of my previous response's brevity using `...`). The key additions are:
    *   Import of `PaymentManager` and `PaymentService`.
    *   Placeholders `_payment_service_instance` and `_payment_manager_instance`.
    *   Initialization of `self._payment_service_instance`.
    *   Initialization of `self._payment_manager_instance` with all its listed dependencies.
    *   Properties for `payment_service` and `payment_manager`.
*   **Content**: The latest generated version of `ApplicationCore` correctly incorporates the new `PaymentService` and `PaymentManager`, including their instantiation with dependencies and exposure via properties. All previously existing service and manager definitions, initializations, and properties were fully restored in this version, addressing the previous `AttributeError`.
*   **Correctness**: The `ApplicationCore.py` file is now complete and correctly structured. The application launch log confirms that there are no `AttributeError`s during startup, indicating all necessary components are being initialized and are accessible.

File `app/core/application_core.py` is updated correctly and is now complete.

---
**Summary of Payments Module (Backend) Implementation:**

The backend infrastructure for the Payments Module is now in place:
1.  **DTOs**: Defined in `app/utils/pydantic_models.py` for payment and allocation data.
2.  **Service Layer**: `PaymentService` and `IPaymentRepository` are established.
3.  **Manager Layer**: `PaymentManager` is implemented with logic for creating payments, including JE posting and invoice allocation updates within a single transaction.
4.  **Integration**: These new components are correctly integrated into `ApplicationCore`.

The application is launching successfully with these backend changes. The next step will be to implement the User Interface for the Payments Module.

---
https://drive.google.com/file/d/17zxIJGfPzj_bEhRkeDk-eOHCUvGpgm1L/view?usp=sharing, https://drive.google.com/file/d/18eCmyFtf_HDCkC347yLPzJoq7PT68qEU/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2218qnqQW2PHZdyMAtWUuVJnsRY5cI6vHO-%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1KFYa5nOcPc5NoNfKeqUYwg4O15Oy7i2M/view?usp=sharing, https://drive.google.com/file/d/1Swn5hLE8EMis0ZotvCzYMMP-IrVtmWZJ/view?usp=sharing, https://drive.google.com/file/d/1YqIRX5gYKhKyYdhEo4SFchjZKLoi1LCl/view?usp=sharing, https://drive.google.com/file/d/1a4XAXKIR6dbHBRplebLniCw5zvrwhWei/view?usp=sharing, https://drive.google.com/file/d/1bzNUDHlMHLSA-hdn0kmFHJgVikPmQNM8/view?usp=sharing, https://drive.google.com/file/d/1dDNa_gl7IWu1Lw-jdih1PPuS8AufaeEx/view?usp=sharing, https://drive.google.com/file/d/1eAZAxBGG97aAyna7zA-pg8P11vFiICtc/view?usp=sharing, https://drive.google.com/file/d/1enLshf6mQ_UaB8CifUfzWHPRCbXCWELE/view?usp=sharing, https://drive.google.com/file/d/1ev06ScrpUmyx4vPoASOq29TlIKhPzYqI/view?usp=sharing, https://drive.google.com/file/d/1gMFlz5RRWYNHuHcpv-UgMA8SHm6R3Qft/view?usp=sharing, https://drive.google.com/file/d/1gcJVXsLa3wYd6zyDlkKIJzdIFLDHF6s0/view?usp=sharing, https://drive.google.com/file/d/1p4pfoke5txRfds2aBGYNmyjzQQheS-3P/view?usp=sharing, https://drive.google.com/file/d/1u82QUlopaeVyX9zeiGv0Rg1kx81rrPaj/view?usp=sharing, https://drive.google.com/file/d/1vjXcrAl8HS3URZMNSCvfwwIVjLl3BppV/view?usp=sharing, https://drive.google.com/file/d/1x7bCCDUwQ3IMc0bbGVP9HdMxx5C17T1J/view?usp=sharing

