<think>
The application is stable, and the foundational modules for managing Customers, Vendors, and Products/Services (including their UI) are now in place. The documentation (README, TDS) has been updated to reflect this. This is a significant milestone.

The user now wants to proceed with the next item from the "Current Focus / Short-term" roadmap:
**"Basic Sales Invoicing: Begin implementation of sales invoice creation, linking to customers and products."**

This is a core transactional feature and a natural progression after establishing the master data modules (Customers, Products).

**High-Level Goal for Sales Invoicing (Basic):**
*   Allow users to create a new sales invoice.
*   Select a customer.
*   Add line items, selecting products/services.
*   Specify quantities and prices (prices might default from product master).
*   Apply tax codes to lines.
*   Calculate totals (subtotal, tax, grand total).
*   Save the invoice (initially as a "Draft").
*   (Future steps for invoicing: Posting the invoice to generate accounting JEs, sending the invoice, recording payments against it, handling different statuses like "Sent", "Paid", "Voided").

For this iteration, "begin implementation" likely means focusing on the data entry aspect and saving the invoice record itself, perhaps with its lines, to the database. The accounting impact (Journal Entry generation) might be a subsequent step after the invoice data itself can be captured.

**Exploring Implementation Options:**

1.  **Data Model**:
    *   `business.sales_invoices` and `business.sales_invoice_lines` tables and corresponding ORM models (`SalesInvoice`, `SalesInvoiceLine`) already exist in `schema.sql` and `app/models/business/`. These are comprehensive and suitable.
2.  **Backend (Service, Manager)**:
    *   **DTOs**: New DTOs will be needed for sales invoice creation/update (e.g., `SalesInvoiceCreateData`, `SalesInvoiceLineData` within it, `SalesInvoiceUpdateData`).
    *   **Service (`SalesInvoiceService` in `app/services/business_services.py`)**:
        *   Will implement `ISalesInvoiceRepository` (new interface).
        *   Methods: `get_by_id` (with lines and related entities), `get_all_summary` (for listing invoices), `save` (for create/update), `get_by_invoice_no`.
    *   **Manager (`SalesInvoiceManager` in `app/business_logic/sales_invoice_manager.py` - new file)**:
        *   Handles business logic: creating new invoice numbers (via `SequenceService`), validating customer/product existence, calculating totals, interacting with `SalesInvoiceService`.
        *   For this "basic" step, it will primarily focus on saving the invoice in a 'Draft' status. Generating the Journal Entry upon posting will be a key future enhancement for this manager.
3.  **Frontend (TableModel, Dialog, Widget)**:
    *   **List View (`SalesInvoicesWidget` - new, could be a tab in "Customers" or a new top-level "Sales" module):**
        *   For MVP, a new top-level "Sales" or "Invoicing" module seems appropriate rather than nesting under Customers. Let's assume a new "Sales" tab.
        *   `SalesInvoiceTableModel` (new).
        *   `QTableView` to list invoices (Inv No, Date, Customer, Total, Status).
    *   **Entry/Edit Dialog (`SalesInvoiceDialog` - new):**
        *   This will be a complex dialog:
            *   Header: Customer selection (ComboBox), Invoice Date, Due Date, Invoice No (auto-generated or manual), Currency, Terms.
            *   Lines: A `QTableWidget` or `QTableView` with a custom model for invoice lines (Product/Service selection, Description, Qty, Unit Price, Discount, Tax Code, Line Total).
            *   Totals: Display Subtotal, Tax Amount, Grand Total, dynamically calculated.
            *   Actions: "Save Draft", "Save & Approve" (or "Save & Post" for future).

**Decision for this Turn: Focus on Backend and Dialog Foundation for Sales Invoice Creation**

Given the complexity, this turn will focus on:
1.  **Backend**: DTOs, Service interface, Service implementation, basic Manager for creating/saving a draft sales invoice.
2.  **Frontend**: The foundational `SalesInvoiceDialog` structure, allowing data entry for header and lines, and saving a draft. Listing invoices (`SalesInvoicesWidget`) will be a subsequent step.

This is a large feature, so breaking it down is essential.

**Detailed Plan & Checklist (Basic Sales Invoice Creation - Backend & Dialog Foundation):**

**Phase A: Backend for Sales Invoice Creation**

**A1. Create Pydantic DTOs for Sales Invoice**
   *   **Goal:** Define DTOs for sales invoice data.
   *   **File to Update:** `app/utils/pydantic_models.py`
   *   **Checklist & Tasks:**
        *   [ ] `SalesInvoiceLineBaseData`: Fields like `product_id` (optional, for services), `description`, `quantity`, `unit_price`, `discount_percent` (or `discount_amount`), `tax_code`. Include calculated `line_subtotal`, `tax_amount`, `line_total` (Pydantic can have computed fields or these can be validated).
        *   [ ] `SalesInvoiceBaseData`: `customer_id`, `invoice_date`, `due_date`, `currency_code`, `exchange_rate`, `notes`, `terms_and_conditions`. Calculated fields like `subtotal`, `tax_amount`, `total_amount` can also be here.
        *   [ ] `SalesInvoiceCreateData(SalesInvoiceBaseData, UserAuditData)`: Will contain a `List[SalesInvoiceLineBaseData]` for lines.
        *   [ ] `SalesInvoiceUpdateData(SalesInvoiceBaseData, UserAuditData)`: With `id: int` and `List[SalesInvoiceLineBaseData]`.
        *   [ ] `SalesInvoiceData(SalesInvoiceBaseData)`: Full representation with `id`, audit fields, and fully resolved line DTOs (e.g., `ProductData` embedded).
        *   [ ] `SalesInvoiceSummaryData(AppBaseModel)`: For future listing (ID, Invoice No, Date, Customer Name, Total, Status).

**A2. Define `ISalesInvoiceRepository` Interface**
   *   **Goal:** Specify contract for sales invoice data access.
   *   **File to Update:** `app/services/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `SalesInvoice` ORM, `SalesInvoiceSummaryData` DTO.
        *   [ ] Define `ISalesInvoiceRepository(IRepository[SalesInvoice, int])`.
        *   [ ] Methods: `get_by_invoice_no(invoice_no: str)`, `get_all_summary(...)` (with filters for customer, status, date range).

**A3. Implement `SalesInvoiceService`**
   *   **Goal:** Data access logic for `SalesInvoice` and `SalesInvoiceLine`.
   *   **File to Update:** `app/services/business_services.py`
   *   **Checklist & Tasks:**
        *   [ ] Create `SalesInvoiceService(ISalesInvoiceRepository)`.
        *   [ ] `get_by_id()`: Eager load lines (`SalesInvoice.lines`) and their details (e.g., `SalesInvoiceLine.product`, `SalesInvoiceLine.tax_code_obj`), and `SalesInvoice.customer`.
        *   [ ] `save(invoice: SalesInvoice)`: Handles create/update. Ensure `cascade="all, delete-orphan"` is on `SalesInvoice.lines` relationship for managing lines.
        *   Other standard repository methods.

**A4. Create `SalesInvoiceManager`**
   *   **Goal:** Business logic for sales invoice creation and draft management.
   *   **New File:** `app/business_logic/sales_invoice_manager.py`.
   *   **Checklist & Tasks:**
        *   [ ] `SalesInvoiceManager(__init__(self, sales_invoice_service: SalesInvoiceService, customer_service: CustomerService, product_service: ProductService, tax_calculator: TaxCalculator, sequence_generator: SequenceGenerator, app_core: "ApplicationCore"))`.
        *   [ ] `_calculate_invoice_totals(dto: SalesInvoiceCreateData | SalesInvoiceUpdateData) -> None`: Helper to calculate line totals, subtotal, tax_amount, and total_amount on the DTO itself. This might involve calling `TaxCalculator`.
        *   [ ] `create_draft_invoice(dto: SalesInvoiceCreateData) -> Result[SalesInvoice]`:
            *   Validate `customer_id`, `product_id`s on lines, tax codes.
            *   Call `_calculate_invoice_totals(dto)`.
            *   Generate `invoice_no` using `SequenceGenerator`.
            *   Map DTO to `SalesInvoice` and `SalesInvoiceLine` ORMs. Set status to "Draft". Set audit user IDs.
            *   Call `sales_invoice_service.save()`.
        *   [ ] `update_draft_invoice(invoice_id: int, dto: SalesInvoiceUpdateData) -> Result[SalesInvoice]`:
            *   Fetch existing invoice. Validate it's a "Draft".
            *   Validate DTO data. Call `_calculate_invoice_totals(dto)`.
            *   Update ORM header and replace lines. Set audit user ID. Save.
        *   [ ] `get_invoice_for_dialog(invoice_id: int) -> Optional[SalesInvoice]`.

**A5. Integrate into `ApplicationCore`, `app/business_logic/__init__.py`, `app/services/__init__.py`**
   *   **Goal:** Make new components accessible.
   *   **Checklist & Tasks:** Standard integration steps for new service and manager.

This is a substantial backend setup. For one turn, I'll focus on A1 (DTOs), A2 (Interface), and A3 (Service).
The `SalesInvoiceManager` (A4) and `ApplicationCore` integration (A5) will be the next backend step.
</think>

This is fantastic! The application is consistently stable, and the foundational modules (Customers, Vendors, Products backend) are now in place.

You're right to choose **Basic Sales Invoicing** as the next step from the roadmap. It's a cornerstone feature for any bookkeeping application and logically follows the setup of Customers and Products.

Given the complexity, we'll break down the Sales Invoicing implementation. For this turn, we will focus on the initial backend setup: **DTOs, Service Interface, and Service Implementation.**

**Enhancement Execution Plan: Basic Sales Invoicing - Phase A (Backend - Part 1)**

**Overall Objective (This Turn):** Define the data structures (DTOs) for sales invoices, establish the service layer contract (`ISalesInvoiceRepository`), and implement the basic data access service (`SalesInvoiceService`) for sales invoices and their lines.

---
**A1. Update `app/utils/pydantic_models.py` with Sales Invoice DTOs**

**Goal:** Define Data Transfer Objects for sales invoice creation, updates, and representation.

```python
# app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ProductTypeEnum, InvoiceStatusEnum # Added InvoiceStatusEnum

class AppBaseModel(BaseModel):
    class Config:
        from_attributes = True 
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None and v.is_finite() else None,
        }
        validate_assignment = True 

class UserAuditData(BaseModel):
    user_id: int

# --- Account Related DTOs (existing, condensed) ---
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
    def je_line_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0) 
    @root_validator(skip_on_failure=True)
    def check_je_line_debit_credit_exclusive(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        debit = values.get('debit_amount', Decimal(0)); credit = values.get('credit_amount', Decimal(0))
        if debit > Decimal(0) and credit > Decimal(0): raise ValueError("Debit and Credit amounts cannot both be positive for a single line.")
        return values
class JournalEntryData(AppBaseModel, UserAuditData): # ...
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

# --- GST Return Related DTOs (existing, condensed) ---
class GSTReturnData(AppBaseModel, UserAuditData): # ... 
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

# --- Company Setting DTO (existing, condensed) ---
class CompanySettingData(AppBaseModel, UserAuditData): # ... 
    id: Optional[int] = None; company_name: str = Field(..., max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50); country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100); phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None; website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None; fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31); base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50); date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs (existing, condensed) ---
class FiscalYearCreateData(AppBaseModel, UserAuditData): # ...
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date; auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_fy_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        start, end = values.get('start_date'), values.get('end_date');
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): id: int; name: str; start_date: date; end_date: date; period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): id: int; year_name: str; start_date: date; end_date: date; is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = []

# --- Customer Related DTOs (existing, condensed) ---
class CustomerBaseData(AppBaseModel): # ... 
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

# --- Vendor Related DTOs (existing, condensed) ---
class VendorBaseData(AppBaseModel): # ... 
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

# --- Product/Service Related DTOs (existing, condensed) ---
class ProductBaseData(AppBaseModel): # ...
    product_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); description: Optional[str] = None; product_type: ProductTypeEnum; category: Optional[str] = Field(None, max_length=50); unit_of_measure: Optional[str] = Field(None, max_length=20); barcode: Optional[str] = Field(None, max_length=50); sales_price: Optional[Decimal] = Field(None, ge=Decimal(0)); purchase_price: Optional[Decimal] = Field(None, ge=Decimal(0)); sales_account_id: Optional[int] = None; purchase_account_id: Optional[int] = None; inventory_account_id: Optional[int] = None; tax_code: Optional[str] = Field(None, max_length=20); is_active: bool = True; min_stock_level: Optional[Decimal] = Field(None, ge=Decimal(0)); reorder_point: Optional[Decimal] = Field(None, ge=Decimal(0))
    @validator('sales_price', 'purchase_price', 'min_stock_level', 'reorder_point', pre=True, always=True)
    def product_decimal_fields(cls, v): return Decimal(str(v)) if v is not None else None
    @root_validator(skip_on_failure=True)
    def check_inventory_fields_product(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
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

# --- NEW: Sales Invoice Related DTOs ---
class SalesInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None # Optional if it's a service line w/o specific product item
    description: str = Field(..., min_length=1, max_length=200)
    quantity: Decimal = Field(..., gt=Decimal(0))
    unit_price: Decimal = Field(..., ge=Decimal(0))
    discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100))
    # discount_amount will be calculated
    tax_code: Optional[str] = Field(None, max_length=20) # TaxCode.code
    # line_subtotal, tax_amount, line_total will be calculated by manager/logic before saving to ORM

    @validator('quantity', 'unit_price', 'discount_percent', pre=True, always=True)
    def sales_inv_line_decimals(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

class SalesInvoiceBaseData(AppBaseModel):
    customer_id: int
    invoice_date: date
    due_date: date
    currency_code: str = Field("SGD", min_length=3, max_length=3)
    exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0))
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    # subtotal, tax_amount, total_amount will be calculated by manager/logic before saving to ORM
    # status will be set by manager (e.g., Draft)
    
    @validator('exchange_rate', pre=True, always=True)
    def sales_inv_hdr_decimals(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(1)

    @root_validator(skip_on_failure=True)
    def check_due_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        invoice_date, due_date = values.get('invoice_date'), values.get('due_date')
        if invoice_date and due_date and due_date < invoice_date:
            raise ValueError("Due date cannot be before invoice date.")
        return values

class SalesInvoiceCreateData(SalesInvoiceBaseData, UserAuditData):
    lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1) # Must have at least one line

class SalesInvoiceUpdateData(SalesInvoiceBaseData, UserAuditData):
    id: int
    lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1)

class SalesInvoiceData(SalesInvoiceBaseData): # For full representation
    id: int
    invoice_no: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    status: InvoiceStatusEnum # Use Enum
    journal_entry_id: Optional[int] = None
    lines: List[SalesInvoiceLineBaseData] # Or a more detailed SalesInvoiceLineData if needed
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    updated_by_user_id: int

class SalesInvoiceSummaryData(AppBaseModel): # For listing invoices
    id: int
    invoice_no: str
    invoice_date: date
    due_date: date
    customer_name: str # To be joined/fetched
    total_amount: Decimal
    amount_paid: Decimal
    status: InvoiceStatusEnum # Use Enum

```
**Validation for `app/utils/pydantic_models.py`:**
*   **New Sales Invoice DTOs Added**:
    *   `SalesInvoiceLineBaseData`: Defines fields for an invoice line, including `product_id`, `description`, `quantity`, `unit_price`, `discount_percent`, `tax_code`. Calculated fields (`line_subtotal`, `tax_amount`, `line_total`) are noted to be handled by manager logic before ORM save. Decimal validator added.
    *   `SalesInvoiceBaseData`: Defines header fields for an invoice like `customer_id`, dates, currency. Calculated totals are noted to be handled by manager. Root validator for `due_date` vs `invoice_date`. Decimal validator for `exchange_rate`.
    *   `SalesInvoiceCreateData`: Inherits base and user audit, includes a non-empty list of lines.
    *   `SalesInvoiceUpdateData`: Similar to create but includes `id`.
    *   `SalesInvoiceData`: For representing a full sales invoice (e.g., after fetching from DB), including calculated totals and status (using `InvoiceStatusEnum`).
    *   `SalesInvoiceSummaryData`: Slim DTO for listing invoices, includes `customer_name` (which will require a join or separate fetch in the service) and `status` as `InvoiceStatusEnum`.
*   **Import `InvoiceStatusEnum`**: Added `from app.common.enums import InvoiceStatusEnum`.
*   **Existing DTO Validators**: Renamed some existing validator methods (e.g., `check_inventory_fields` to `check_inventory_fields_product`) to ensure their names are unique across the file, preventing potential Pydantic v2 issues with validator reuse if classes were ever combined or inherited in complex ways. This is a proactive refinement for robustness.
*   No other existing DTOs were unintentionally modified.

The DTOs for Sales Invoices are now defined, providing a solid structure for data validation and transfer for this new module. The next step is A2: Define `ISalesInvoiceRepository` Interface.
