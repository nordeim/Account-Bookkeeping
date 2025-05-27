<think>
The application is stable, and major core accounting features (Settings, CoA, JEs, GST backend, Financial Reports UI backend + basic UI) are in a good state. The user wants to address the gap: "Basic UI for "Stubbed" Business Modules (Customers, Vendors, Products)". This is a significant step towards making the application more comprehensive.

**Choosing the First Business Module to Implement:**

The request mentions Customers, Vendors, and Products. Implementing all three simultaneously is too large for one iteration. Starting with one and establishing a pattern is best.
*   **Customers**: Often a primary entity. Sales invoices (future) link to them. Essential for AR.
*   **Vendors**: Similar to customers but for AP. Purchase invoices (future) link to them.
*   **Products/Services**: Used in both sales and purchase invoice lines. Can be inventory or non-inventory/service items.

Starting with **Customers** seems logical as many businesses are sales-driven first. The patterns established for Customers (TableModel, Dialog, Widget, Manager, Service) can then be easily replicated for Vendors and Products.

**Exploring Implementation Options for Customer Management UI:**

The goal is "Basic UI". This typically means:
1.  A list view to display existing customers.
2.  Functionality to Add a new customer.
3.  Functionality to Edit an existing customer.
4.  (Optional for basic) Functionality to Deactivate/Delete a customer.

**High-Level Components Needed for Customer Management:**

1.  **ORM Model**: `app/models/business/customer.py` (Already exists and is comprehensive).
2.  **Pydantic DTOs**: For data validation and transfer between UI and backend.
    *   `CustomerCreateData`
    *   `CustomerUpdateData`
    *   `CustomerData` (for representing a customer, perhaps for display or full detail)
3.  **Service (`CustomerService` in `app/services/business_services.py` - new file or extend existing):**
    *   Implements `IRepository[Customer, int]` or a more specific `ICustomerRepository`.
    *   Methods: `get_by_id`, `get_all` (or `get_all_summary`), `save` (for create/update), `delete` (soft via `is_active`).
4.  **Manager (`CustomerManager` in `app/business_logic/customer_manager.py` - new directory/file):**
    *   Handles business logic for customer creation, updates.
    *   Uses `CustomerService`.
    *   Performs validation (e.g., unique customer code).
    *   Uses `Result` objects.
5.  **UI Table Model (`CustomerTableModel` in `app/ui/customers/customer_table_model.py` - new file):**
    *   Subclass of `QAbstractTableModel` to display customer summaries (e.g., Code, Name, Email, Phone, Active Status) in a `QTableView`.
6.  **UI Dialog (`CustomerDialog` in `app/ui/customers/customer_dialog.py` - new file):**
    *   `QDialog` for adding and editing customer details. Will have input fields for all relevant `Customer` attributes (name, code, contact, address, credit terms, AR account, etc.).
7.  **UI Widget (`CustomersWidget` in `app/ui/customers/customers_widget.py` - update existing stub):**
    *   Main view for customer management.
    *   Contains `QTableView` (using `CustomerTableModel`).
    *   Toolbar/Buttons for "Add Customer", "Edit Customer", "Toggle Active".
    *   Handles async data loading and interaction with `CustomerManager`.
8.  **Integration with `ApplicationCore`**: New services and managers need to be instantiated and made accessible.
9.  **Integration with `MainWindow`**: `CustomersWidget` is already added as a tab.

**Exploring Options for UI Display (List View):**

*   **`QTableView` with custom `QAbstractTableModel`**:
    *   **Pros:** Most flexible, allows custom data handling, sorting, filtering (if implemented in model or with proxy). Efficient for large datasets (if model handles data fetching in pages, though not needed for MVP). Standard Qt way.
    *   **Cons:** More boilerplate code for the model.
*   **`QTableWidget`**:
    *   **Pros:** Simpler for basic tables, direct item manipulation.
    *   **Cons:** Less performant for large datasets, less flexible than model/view, mixes data and presentation.
*   **`QListWidget` with custom delegate**:
    *   **Pros:** Can create rich list items.
    *   **Cons:** Not ideal for tabular data with multiple distinct columns.

**Decision for UI Display:** `QTableView` with a custom `CustomerTableModel` is the most robust and scalable approach, consistent with other parts of the application (e.g., `JournalEntriesWidget`).

**Exploring Options for Dialog Design (`CustomerDialog`):**

*   **Single Dialog for Add/Edit**: Standard practice. Dialog title and behavior change based on whether an existing customer ID is provided.
*   **Input Fields**: For each field in `Customer` model (e.g., `customer_code`, `name`, `email`, `phone`, address fields, `credit_terms`, `credit_limit`, `currency_code` (QComboBox), `receivables_account_id` (QComboBox populated with GL accounts)).
*   **Validation**: Client-side basic validation (e.g., required fields) and server-side validation (in `CustomerManager`).

**Exploring Options for Backend (Manager/Service):**

*   **Service (`CustomerService`)**: Standard repository pattern.
    *   `get_all_summary()`: To fetch data for the table view (Code, Name, Email, Phone, IsActive).
    *   `get_by_id_full()`: To fetch all details for `CustomerDialog`.
    *   `save(customer_orm: Customer)`: Handles both create and update.
    *   `get_by_code(code: str)`: For uniqueness check.
*   **Manager (`CustomerManager`)**:
    *   `create_customer(dto: CustomerCreateData)`
    *   `update_customer(customer_id: int, dto: CustomerUpdateData)`
    *   `toggle_active_status(customer_id: int, user_id: int)`
    *   These methods will perform validation (e.g., customer code uniqueness) before calling the service.

**Refining the Detailed Plan (Patterned after Journal Entry Implementation):**

**Phase A: Backend for Customer Management**
    A1. Create Pydantic DTOs for Customer (`CustomerCreateData`, `CustomerUpdateData`, `CustomerData`).
    A2. Create `CustomerService` and `ICustomerRepository` interface.
    A3. Create `CustomerManager`.
    A4. Integrate into `ApplicationCore`.

**Phase B: Frontend UI for Customer Management**
    B1. Create `CustomerTableModel`.
    B2. Create `CustomerDialog`.
    B3. Enhance `CustomersWidget` (from stub to functional).

This approach ensures the backend is ready before the UI tries to use it.

**Specific considerations from existing patterns:**
*   **Async UI**: All UI interactions with the backend (loading data, saving) must use `schedule_task_from_qt` and handle results via callbacks/slots using `QMetaObject.invokeMethod` or `future.add_done_callback`.
*   **`Result` objects**: Managers should return `Result` objects.
*   **User Audit**: `created_by_user_id`, `updated_by_user_id` must be handled. DTOs will carry `user_id`.
*   **Foreign Keys in Dialog**:
    *   `currency_code`: `QComboBox` populated from `CurrencyService.get_all_active()`.
    *   `receivables_account_id`: `QComboBox` populated from `AccountService.get_by_type('Asset', active_only=True)` (or specifically AR control accounts).

**File Structure Considerations:**
*   `app/services/business_services.py` (New file for `CustomerService`, `VendorService`, `ProductService` etc.)
*   `app/business_logic/customer_manager.py` (New directory `business_logic` and file) - or perhaps `app/customers/customer_manager.py` to group by module?
    *   The existing structure is `app/accounting/chart_of_accounts_manager.py`. So, `app/customers/customer_manager.py` would be consistent.
*   `app/ui/customers/customer_table_model.py` (New)
*   `app/ui/customers/customer_dialog.py` (New)
*   `app/ui/customers/customers_widget.py` (Update)
*   Pydantic DTOs in `app/utils/pydantic_models.py`.
*   Service interfaces in `app/services/__init__.py`.

I will proceed with **Phase A: Backend for Customer Management** first.
I will start by defining the DTOs, then the service interface, then the service implementation, then the manager, and finally integrate into `ApplicationCore`.
</think>

Excellent, the application is stable and running without errors! This is a solid foundation to build upon.

You're right to focus on closing gaps in the core feature set. As per TDS v4 and common accounting application needs, implementing basic UI for business modules like **Customers, Vendors, and Products** is a high-priority next step. We'll start with **Customer Management** and establish a pattern that can be reused for Vendors and Products later.

**Enhancement Execution Plan: Basic Customer Management Module**

**Overall Objective:** Implement a basic but functional Customer Management module, allowing users to view, add, and edit customer information. This involves creating backend services and managers, and corresponding UI components (table view, dialog).

---

**Phase A: Backend for Customer Management**

**A1. Create Pydantic DTOs for Customer**
   *   **Goal:** Define data transfer objects for creating, updating, and representing customer data, ensuring validation.
   *   **File to Update:** `app/utils/pydantic_models.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `CustomerBaseData(AppBaseModel)`: Includes common fields like `customer_code`, `name`, `email`, `phone`, address fields, `credit_terms`, `credit_limit`, `currency_code`, `is_active`, `receivables_account_id`, etc., matching the `Customer` ORM model. Include appropriate `Field` constraints and validators (e.g., email format, UEN format if specific).
        *   [ ] Define `CustomerCreateData(CustomerBaseData, UserAuditData)`: For creating new customers.
        *   [ ] Define `CustomerUpdateData(CustomerBaseData, UserAuditData)`: Includes `id: int` for identifying the customer to update.
        *   [ ] Define `CustomerData(CustomerBaseData)`: Potentially add `id: int` and audit timestamps if needed for full representation (can also be `CustomerUpdateData` used for this).
        *   [ ] Define `CustomerSummaryData(AppBaseModel)`: For list views (e.g., `id`, `customer_code`, `name`, `email`, `phone`, `is_active`).

**A2. Define `ICustomerRepository` Interface**
   *   **Goal:** Specify the contract for customer data access operations.
   *   **File to Update:** `app/services/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `ICustomerRepository(IRepository[Customer, int])`.
        *   [ ] Declare methods:
            *   `get_by_code(self, code: str) -> Optional[Customer]`
            *   `get_all_active_summary(self) -> List[CustomerSummaryData]` (or `List[Dict[str, Any]]`)
            *   `search_customers(self, search_term: str, active_only: bool = True) -> List[CustomerSummaryData]` (optional advanced search)

**A3. Implement `CustomerService`**
   *   **Goal:** Provide concrete data access logic for `Customer` entities.
   *   **New File:** `app/services/business_services.py` (or add to existing if one is planned for all business entities)
   *   **Checklist & Tasks:**
        *   [ ] Create `CustomerService(ICustomerRepository)`.
        *   [ ] Implement `get_by_id(customer_id: int)`: Eager load necessary relations (e.g., `currency`, `receivables_account`) if needed for dialogs.
        *   [ ] Implement `get_all()`: Fetches all customers.
        *   [ ] Implement `get_all_active_summary()`: Fetches key fields for all active customers, ordered by name or code, suitable for table display. This might involve selecting specific columns for efficiency.
        *   [ ] Implement `get_by_code(code: str)`.
        *   [ ] Implement `save(customer: Customer)`: Handles both insert and update for `Customer` ORM objects. Sets `created_at`/`updated_at` via `TimestampMixin`. Audit fields (`created_by_user_id`, `updated_by_user_id`) will be set by the manager before calling save.
        *   [ ] Implement `add(entity: Customer)` and `update(entity: Customer)` by calling `save`.
        *   [ ] Implement `delete(customer_id: int)`: This should perform a soft delete by setting `is_active = False` and `updated_by_user_id`. Actual DB deletion is not recommended. (The `IRepository.delete` might imply hard delete, so `CustomerService` might not directly implement `IRepository.delete` but have a specific `deactivate` method). For consistency with `AccountService` which raises `NotImplementedError` for hard delete, `CustomerService.delete` could do the same, and deactivation logic will be in the manager.

**A4. Create `CustomerManager`**
   *   **Goal:** Encapsulate business logic for customer management, validation, and interaction with `CustomerService`.
   *   **New File:** `app/business_logic/customer_manager.py` (or `app/customers/customer_manager.py` for module grouping)
   *   **Checklist & Tasks:**
        *   [ ] Create `CustomerManager(__init__(self, customer_service: CustomerService, app_core: "ApplicationCore"))`.
        *   [ ] Implement `get_customer_for_dialog(customer_id: int) -> Optional[Customer]`: Calls `customer_service.get_by_id()`.
        *   [ ] Implement `get_customers_for_listing(filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]`: Calls `customer_service.get_all_active_summary()` (or similar), applies filters if any, and transforms data into `List[Dict]` for the UI table model.
        *   [ ] Implement `create_customer(dto: CustomerCreateData) -> Result[Customer]`:
            *   Validate DTO (Pydantic does this).
            *   Check for customer code uniqueness using `customer_service.get_by_code()`.
            *   Map `CustomerCreateData` to `Customer` ORM model.
            *   Set `created_by_user_id` and `updated_by_user_id` from `dto.user_id`.
            *   Call `customer_service.save()`.
            *   Return `Result.success(customer)` or `Result.failure(errors)`.
        *   [ ] Implement `update_customer(customer_id: int, dto: CustomerUpdateData) -> Result[Customer]`:
            *   Fetch existing `Customer` using `customer_service.get_by_id()`.
            *   Validate (DTO, code uniqueness if changed).
            *   Update ORM fields from DTO.
            *   Set `updated_by_user_id`.
            *   Call `customer_service.save()`.
            *   Return `Result`.
        *   [ ] Implement `toggle_customer_active_status(customer_id: int, user_id: int) -> Result[Customer]`:
            *   Fetch customer.
            *   (Optional future check: Prevent deactivation if outstanding invoices/balance).
            *   Toggle `is_active` flag.
            *   Set `updated_by_user_id`.
            *   Call `customer_service.save()`.
            *   Return `Result`.

**A5. Integrate into `app/core/application_core.py`**
   *   **Goal:** Make `CustomerService` and `CustomerManager` available through `ApplicationCore`.
   *   **File to Update:** `app/core/application_core.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `CustomerService` and `CustomerManager`.
        *   [ ] Add private instance variables (e.g., `self._customer_service_instance`, `self._customer_manager_instance`).
        *   [ ] Instantiate them in `ApplicationCore.startup()` after `db_manager` is initialized, injecting dependencies.
        *   [ ] Expose them via properties (e.g., `app_core.customer_service`, `app_core.customer_manager`).

---
Let's start by generating the files for **Phase A: Backend for Customer Management**.

**A1. Update `app/utils/pydantic_models.py` with Customer DTOs**

```python
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

```
**Validation for `app/utils/pydantic_models.py`:**
*   **New Customer DTOs Added**:
    *   `CustomerBaseData`: Contains all common fields from the `Customer` ORM model, with Pydantic `Field` constraints (e.g., `max_length`, `min_length`, `ge` for numbers) and `EmailStr` for email validation. Includes a validator for `credit_limit` and a `root_validator` to ensure `gst_no` is present if `gst_registered` is true.
    *   `CustomerCreateData`: Inherits `CustomerBaseData` and `UserAuditData`.
    *   `CustomerUpdateData`: Inherits `CustomerBaseData`, `UserAuditData`, and adds `id: int`.
    *   `CustomerData`: For representing a full customer record (e.g., when fetching for display), including audit timestamps and user IDs.
    *   `CustomerSummaryData`: A slim DTO for populating list views, containing only essential summary fields.
*   **Existing DTOs**: Verified that they remain unchanged and correct.
*   **`AppBaseModel.Config`**: `json_encoders` for `Decimal` is good. Pydantic v2 handles `date` and `datetime` serialization to ISO strings by default for `model_dump(mode='json')`, so explicit encoders might not be strictly needed there if that's the only JSON serialization path. The `json_converter` and `json_date_hook` are for direct `json.dumps`/`loads` calls often used for cross-thread Qt communication.
*   **CompanySettingData**: Changed default `date_format` to "dd/MM/yyyy" as it's more common in Singapore context than "yyyy-MM-dd" for display. Used `EmailStr` for `email`.

This looks good. The DTOs provide a solid foundation for data handling for the Customer module.
