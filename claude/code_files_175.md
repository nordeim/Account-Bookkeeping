<think>
The application launches successfully. The reporting options (comparative periods, zero-balance toggle) for BS/P&L in `ReportsWidget` are integrated. The on-screen display for BS/P&L via `QTreeView` has also been enhanced.

**Current Project Status Recap:**

*   **Sales Invoicing**: Fully functional for draft CRUD, posting with JE, list view, dialog with "Save & Approve".
*   **User and Role Management UI**: Fully functional.
*   **Reporting**:
    *   `ReportsWidget` UI enhanced with options for comparative periods (BS/P&L) and zero-balance accounts (BS).
    *   On-screen display for BS & P&L in `QTreeView` improved with better structure and formatting.
    *   PDF/Excel export for BS & P&L has enhanced formatting.
    *   TB & GL display/export are functional with simpler table views/exports.
*   All previously implemented features remain stable.

**Next Step Identification (from Roadmap):**

Roadmap - "Current Focus / Short-term":
1.  **Sales Invoicing**:
    *   Implement "Save & Approve" button functionality in `SalesInvoiceDialog`. <-- DONE
    *   Enhance line item entry (e.g., better product search/selection). <-- Basic enhancement done. Advanced popup search is still an option.
    *   **(Future)** Handle inventory updates upon posting.
2.  **Refine Reporting**:
    *   Improve PDF/Excel export formatting and layout. <-- DONE for BS/P&L. Could extend to TB/GL.
    *   Add more reporting options/filters. <-- DONE for BS/P&L comparative/zero-balance. Could add more dimension/status filters.
3.  **Purchase Invoicing**: Begin implementation. <-- This is the next major new module.

Given the current state:
*   Sales Invoicing is quite complete for its initial scope (drafts, posting). Inventory updates are explicitly marked "Future". Advanced product search is a "nice-to-have" polish for later.
*   Reporting has seen significant refinement in display and export for key statements, and new options. Further refinements can be iterative.
*   User/Role Management is complete.

The most impactful next step according to the roadmap would be to **begin implementation of Purchase Invoicing**. This is a substantial new module.

**Plan for this Turn: Begin Purchase Invoicing - Part 1 (Models, DTOs, Service Interface, Basic Manager & Service Stubs).**

This is analogous to how Sales Invoicing was started: laying the foundational backend structures.

**Objective:**
Create the necessary data models (SQLAlchemy), Data Transfer Objects (Pydantic), the repository interface for Purchase Invoices (`IPurchaseInvoiceRepository`), and initial stubs for `PurchaseInvoiceService` and `PurchaseInvoiceManager`.

**Detailed Plan & Checklist:**

**I. Models (`app/models/business/purchase_invoice.py` - already exists, review and confirm completeness):**
    *   [ ] `PurchaseInvoice(Base, TimestampMixin)`:
        *   Fields: `id`, `invoice_no` (vendor's), `our_ref_no` (our internal ref, maybe from sequence), `vendor_id`, `invoice_date`, `due_date`, `currency_code`, `exchange_rate`, `subtotal`, `tax_amount`, `total_amount`, `amount_paid`, `status` (enum: Draft, Approved, Paid, Voided etc.), `notes`, `journal_entry_id`, audit fields.
        *   Relationships: `vendor`, `currency`, `journal_entry`, `lines` (cascade delete).
    *   [ ] `PurchaseInvoiceLine(Base, TimestampMixin)`:
        *   Fields: `id`, `invoice_id`, `line_number`, `product_id` (optional), `description`, `quantity`, `unit_price`, `discount_percent`, `discount_amount`, `line_subtotal`, `tax_code`, `tax_amount`, `line_total`, `dimension1_id`, `dimension2_id`.
        *   Relationships: `invoice`, `product`, `tax_code_obj`, `dimension1`, `dimension2`.
    *   **Self-Correction**: The existing `purchase_invoice.py` (from `project_codebase_files_set-4.md`) has `invoice_no` (our unique ref) and `vendor_invoice_no`. This is good. It needs `our_ref_no` to be managed by a sequence if `invoice_no` is strictly the vendor's. Let's assume `invoice_no` in the model is *our* unique internal number for now, and `vendor_invoice_no` is for the supplier's document number.
    *   **Decision**: Review `app/models/business/purchase_invoice.py`. It seems well-defined already. No changes needed unless discrepancies found against `schema.sql`.

**II. Data Transfer Objects (`app/utils/pydantic_models.py`)**:
    *   [ ] Define `PurchaseInvoiceLineBaseData(AppBaseModel)`: Similar to `SalesInvoiceLineBaseData` (product_id, description, quantity, unit_price, discount_percent, tax_code, dimensions).
    *   [ ] Define `PurchaseInvoiceBaseData(AppBaseModel)`: Similar to `SalesInvoiceBaseData` (vendor_id, vendor_invoice_no, invoice_date, due_date, currency_code, exchange_rate, notes).
    *   [ ] Define `PurchaseInvoiceCreateData(PurchaseInvoiceBaseData, UserAuditData)`: Includes `lines: List[PurchaseInvoiceLineBaseData]`.
    *   [ ] Define `PurchaseInvoiceUpdateData(PurchaseInvoiceBaseData, UserAuditData)`: Includes `id: int`, `lines`.
    *   [ ] Define `PurchaseInvoiceSummaryData(AppBaseModel)`: For list views (id, our_invoice_no, vendor_invoice_no, invoice_date, vendor_name, total_amount, status).
    *   [ ] Define `PurchaseInvoiceData(PurchaseInvoiceBaseData)`: For full representation including calculated fields and status.

**III. Service Interface (`app/services/__init__.py`)**:
    *   [ ] Define `IPurchaseInvoiceRepository(IRepository[PurchaseInvoice, int])`:
        *   `get_by_our_ref_no(our_ref_no: str) -> Optional[PurchaseInvoice]`
        *   `get_by_vendor_invoice_no(vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]` (to check for duplicates from same vendor)
        *   `get_all_summary(...) -> List[PurchaseInvoiceSummaryData]` (with filters for vendor, status, dates, pagination).

**IV. Service Implementation (`app/services/business_services.py`)**:
    *   [ ] Create `PurchaseInvoiceService(IPurchaseInvoiceRepository)`:
        *   Implement `get_by_id` (eager load lines, vendor, currency, JE).
        *   Implement `get_all_summary` (select specific columns, join with vendor, map to DTO).
        *   Implement `get_by_our_ref_no` (or use `invoice_no` if that's our internal ref).
        *   Implement `get_by_vendor_invoice_no`.
        *   Implement `save` (for create/update).
        *   Implement `add`, `update`, `delete` (delete should prevent if posted, defer to manager).

**V. Manager Stub (`app/business_logic/purchase_invoice_manager.py` - New File)**:
    *   [ ] Create `PurchaseInvoiceManager`:
        *   `__init__` with dependencies: `PurchaseInvoiceService`, `VendorService`, `ProductService`, `TaxCodeService`, `TaxCalculator`, `SequenceService`, `AccountService`, `ConfigurationService`, `ApplicationCore`.
        *   Stub methods like `create_draft_purchase_invoice`, `update_draft_purchase_invoice`, `post_purchase_invoice`, `get_invoice_for_dialog`, `get_invoices_for_listing`.

**VI. Update `ApplicationCore` (`app/core/application_core.py`)**:
    *   [ ] Import `PurchaseInvoiceService` and `PurchaseInvoiceManager`.
    *   [ ] Add placeholders and properties for them.
    *   [ ] Instantiate them in `startup()`.

**VII. Update `__init__.py` files**:
    *   [ ] `app/services/__init__.py`: Export `IPurchaseInvoiceRepository` and `PurchaseInvoiceService`.
    *   [ ] `app/business_logic/__init__.py`: Export `PurchaseInvoiceManager`.

This will lay all the necessary backend groundwork before any UI is created for Purchase Invoices. The model `app/models/business/purchase_invoice.py` exists and seems robust from set-4, so it mostly needs DTOs and service/manager structure.
</think>

The application is running well, and significant progress has been made on Sales Invoicing, User/Role Management, and Reporting.

As per the roadmap, the next major undertaking is to **begin implementation of Purchase Invoicing**. This will follow a similar pattern to Sales Invoicing: first, lay the backend foundations (Models, DTOs, Service, Manager), then build the UI.

**Plan for this Turn: Purchase Invoicing - Part 1 (Models Review, DTOs, Service Interface, Basic Service/Manager Stubs)**

**Objective:**
1.  Review the existing Purchase Invoice related ORM models for completeness.
2.  Define Data Transfer Objects (DTOs) for purchase invoice data.
3.  Define the `IPurchaseInvoiceRepository` interface.
4.  Create initial implementations/stubs for `PurchaseInvoiceService` and `PurchaseInvoiceManager`.
5.  Integrate these new components into `ApplicationCore` and relevant `__init__.py` files.

**Execution Plan:**

**I. Review ORM Models (`app/models/business/purchase_invoice.py`)**
    *   The file `app/models/business/purchase_invoice.py` (from `project_codebase_files_set-4.md`) defines `PurchaseInvoice` and `PurchaseInvoiceLine`.
    *   `PurchaseInvoice`: Includes `invoice_no` (which we'll use as our internal reference, generated by a sequence) and `vendor_invoice_no` (for the supplier's actual invoice number). This distinction is good. Other fields like `vendor_id`, dates, currency, totals, status, `journal_entry_id`, audit fields, and relationships seem appropriate.
    *   `PurchaseInvoiceLine`: Similar to `SalesInvoiceLine`, with fields for product, description, qty, price, discount, tax, totals, and dimensions. Relationships to `PurchaseInvoice` and `Product` are present.
    *   **Action**: No changes seem immediately necessary to the ORM models themselves based on the current definition. They appear suitable.
    *   **Checklist**: [X] Models reviewed and deemed suitable.

**II. Create Data Transfer Objects (DTOs) in `app/utils/pydantic_models.py`**
    *   `PurchaseInvoiceLineBaseData`: Similar to `SalesInvoiceLineBaseData` (product_id, description, quantity, unit_price, discount_percent, tax_code, dimension1_id, dimension2_id).
    *   `PurchaseInvoiceBaseData`: vendor_id, vendor_invoice_no (optional, as it might be entered later), invoice_date, due_date, currency_code, exchange_rate, notes.
    *   `PurchaseInvoiceCreateData(PurchaseInvoiceBaseData, UserAuditData)`: Includes `lines: List[PurchaseInvoiceLineBaseData]`.
    *   `PurchaseInvoiceUpdateData(PurchaseInvoiceBaseData, UserAuditData)`: Includes `id: int`, `lines`.
    *   `PurchaseInvoiceData(PurchaseInvoiceBaseData)`: Full representation with our `invoice_no`, calculated totals, status, JE link, audit fields, and lines.
    *   `PurchaseInvoiceSummaryData(AppBaseModel)`: For list views (id, our_invoice_no, vendor_invoice_no, invoice_date, vendor_name, total_amount, status).
    *   **Checklist**: [X] All necessary Purchase Invoice DTOs defined.

**III. Define Service Interface in `app/services/__init__.py`**
    *   Define `IPurchaseInvoiceRepository(IRepository[PurchaseInvoice, int])`.
    *   Abstract methods:
        *   `get_by_internal_ref_no(internal_ref_no: str) -> Optional[PurchaseInvoice]` (corresponds to `invoice_no` in the model).
        *   `get_by_vendor_and_vendor_invoice_no(vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]` (for checking duplicates).
        *   `get_all_summary(...) -> List[PurchaseInvoiceSummaryData]` (with filters for vendor, status, dates, pagination).
    *   **Checklist**: [X] Interface defined with key methods.

**IV. Implement Service Stubs/Basics in `app/services/business_services.py`**
    *   Create `PurchaseInvoiceService(IPurchaseInvoiceRepository)`.
    *   Implement `__init__`.
    *   Implement `get_by_id` (eager loading lines, vendor, currency, etc.).
    *   Implement `get_all_summary` (selecting specific columns, joining with `Vendor` for name, mapping to DTO, handling filters and pagination).
    *   Implement `get_by_internal_ref_no`.
    *   Implement `get_by_vendor_and_vendor_invoice_no`.
    *   Implement `save` (generic create/update).
    *   Implement `add`, `update`, `delete` (basic implementations, manager will add business rules).
    *   **Checklist**: [X] Service class created. [X] Core data retrieval methods implemented. [X] Basic CUD methods implemented.

**V. Create Manager Stub in `app/business_logic/purchase_invoice_manager.py` (New File)**
    *   Create `PurchaseInvoiceManager`.
    *   `__init__` with all necessary dependencies (similar to `SalesInvoiceManager` but with `VendorService`, `PurchaseInvoiceService`, and default A/P, Purchase Expense, GST Input accounts from config).
    *   Stub out key methods:
        *   `create_draft_purchase_invoice(dto: PurchaseInvoiceCreateData) -> Result[PurchaseInvoice]`
        *   `update_draft_purchase_invoice(invoice_id: int, dto: PurchaseInvoiceUpdateData) -> Result[PurchaseInvoice]`
        *   `post_purchase_invoice(invoice_id: int, user_id: int) -> Result[PurchaseInvoice]`
        *   `get_invoice_for_dialog(invoice_id: int) -> Optional[PurchaseInvoice]`
        *   `get_invoices_for_listing(...) -> Result[List[PurchaseInvoiceSummaryData]]`
    *   **Checklist**: [X] Manager class created. [X] `__init__` defined with dependencies. [X] Key methods stubbed.

**VI. Update `ApplicationCore` (`app/core/application_core.py`)**
    *   Import `PurchaseInvoiceService` and `PurchaseInvoiceManager`.
    *   Add service and manager instance placeholders and property getters for them.
    *   Instantiate `PurchaseInvoiceService` and `PurchaseInvoiceManager` in the `startup()` method, injecting dependencies.
    *   **Checklist**: [X] Imports added. [X] Placeholders and properties added. [X] Instances created in `startup`.

**VII. Update `__init__.py` files**
    *   `app/services/__init__.py`: Export `IPurchaseInvoiceRepository` and `PurchaseInvoiceService`.
    *   `app/business_logic/__init__.py`: Export `PurchaseInvoiceManager`.
    *   **Checklist**: [X] Exports added to relevant `__init__` files.

This structured approach will establish the backend foundation for the Purchase Invoicing module.

I will now generate the complete updated files.

---
**1. Update `app/utils/pydantic_models.py`**
```python
# app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ProductTypeEnum, InvoiceStatusEnum # Already includes InvoiceStatusEnum

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
    name: str = Field(..., min_
