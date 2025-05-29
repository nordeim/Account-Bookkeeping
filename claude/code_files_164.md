<think>
The application launches successfully. User Management Part 3 (implementing `UserPasswordDialog` and integrating it) is complete and stable.

**Current Project Status Recap:**

*   **User Management UI**:
    *   `UserManagementWidget`: Lists users. Actions: Add User (launches `UserDialog`), Edit User (launches `UserDialog`), Toggle Active User, Change Password (launches `UserPasswordDialog`).
    *   `UserDialog`: Supports creating new users and editing existing users, including role assignments.
    *   `UserPasswordDialog`: Supports changing a user's password.
    *   `SecurityManager`: Contains backend methods for all these operations.
*   All previously implemented features remain stable.

**Next Step Identification (from Roadmap):**

Roadmap Item: **"User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions."
We have substantially completed the "User Management" part. The next logical component is "Role Management" and then "Permission Assignment to Roles".

**Plan for this Turn: Role and Permission Management UI - Part 1 (Role Listing and Basic CRUD Dialog).**

**Objective:**
1.  Create a new sub-tab within `SettingsWidget` for "Role Management" (alongside "Users").
2.  This tab will list existing roles.
3.  Implement a `RoleDialog` to allow adding new roles and editing existing role names/descriptions.
4.  Permission assignment to roles will be Part 2 for this sub-module.

**Detailed Plan & Checklist:**

**I. Backend Preparation (`SecurityManager` and DTOs):**

1.  **DTOs (`app/utils/pydantic_models.py`)**:
    *   `RoleData(AppBaseModel)`: `id, name, description` - Already exists.
    *   [ ] `RoleCreateData(AppBaseModel)`: `name: str = Field(..., min_length=3, max_length=50)`, `description: Optional[str] = Field(None, max_length=200)`. (No `UserAuditData` for roles as they are system-level, though one could argue an admin user ID should be logged).
    *   [ ] `RoleUpdateData(RoleCreateData)`: `id: int`.
    *   [ ] `PermissionData(AppBaseModel)`: `id: int`, `code: str`, `description: Optional[str] = None`, `module: str`. (For listing permissions in RoleDialog later).

2.  **`SecurityManager` (`app/core/security_manager.py`)**:
    *   `get_all_roles() -> List[Role]` - Already exists.
    *   [ ] Add `async def get_role_by_id(self, role_id: int) -> Optional[Role]`: Fetch role by ID (eager load permissions for Part 2).
    *   [ ] Add `async def create_role(self, dto: RoleCreateData, current_admin_user_id: int) -> Result[Role]`:
        *   Check for role name uniqueness.
        *   Create and save `Role` ORM.
    *   [ ] Add `async def update_role(self, dto: RoleUpdateData, current_admin_user_id: int) -> Result[Role]`:
        *   Fetch role. Check for name uniqueness if name changed. Update name/description. Save.
    *   [ ] Add `async def delete_role(self, role_id: int, current_admin_user_id: int) -> Result[None]`:
        *   Check if role is assigned to any users. If so, prevent deletion or offer to reassign users.
        *   Check if it's a system-critical role (e.g., "Administrator") that shouldn't be deleted.
        *   Delete role and its entries in `core.role_permissions`.
    *   [ ] Add `async def get_all_permissions() -> List[PermissionData]`: Fetch all permissions, map to `PermissionData` DTOs. (For Part 2 - permission assignment UI).

**II. UI Implementation (`app/ui/settings/` and new files):**

1.  **Create `app/ui/settings/role_management_widget.py`**:
    *   [ ] Define `RoleManagementWidget(QWidget)`.
    *   [ ] UI: Toolbar (Add, Edit, Delete Role), `QTableView` (`self.roles_table`).
    *   [ ] Model: `RoleTableModel` (to be created).
    *   [ ] Load roles (`_load_roles`) using `SecurityManager.get_all_roles()`. Map to `RoleData` for the model.
    *   [ ] Slots for actions, launching `RoleDialog`.
    *   [ ] `_update_action_states` based on selection (e.g., can't delete "Administrator").

2.  **Create `app/ui/settings/role_table_model.py`**:
    *   [ ] `RoleTableModel(QAbstractTableModel)` to display `RoleData`. Columns: Name, Description.

3.  **Create `app/ui/settings/role_dialog.py`**:
    *   [ ] `RoleDialog(QDialog)`.
    *   [ ] Fields for `RoleCreateData` / `RoleUpdateData` (name, description).
    *   [ ] **Permissions Assignment (Part 2)**: For this turn, this section will be a placeholder or omitted. A `QListWidget` or `QTableView` with checkboxes will be used later.
    *   [ ] Load existing role data for editing.
    *   [ ] On save, call `SecurityManager.create_role` or `update_role`.

4.  **Update `SettingsWidget` (`app/ui/settings/settings_widget.py`)**:
    *   [ ] The `SettingsWidget` already uses a `QTabWidget`. Add a new "Roles" tab.
    *   [ ] Instantiate and add `RoleManagementWidget` to this new tab.

5.  **Update `app/ui/settings/__init__.py`**:
    *   [ ] Export new widget, dialog, model classes for roles.

**Focus for *this* turn (Role Management - Part 1):**
*   DTOs: `RoleCreateData`, `RoleUpdateData`, `PermissionData`.
*   `SecurityManager`: Methods `get_role_by_id()`, `create_role()`, `update_role()`, `delete_role()`, `get_all_permissions()`.
*   `RoleManagementWidget`: Basic structure, table view, toolbar (actions for Add, Edit, Delete). Delete action might be stubbed if user reassignment is complex.
*   `RoleTableModel`: To display role info.
*   `RoleDialog`: For creating/editing role name and description *only*. Permission assignment UI will be a placeholder.
*   `SettingsWidget`: Add the "Roles" tab.

This approach breaks down Role and Permission management into smaller, manageable pieces.
</think>

The application continues to run smoothly. User Management UI (listing, add/edit dialog, password change dialog, toggle active status) is successfully integrated.

The next logical step from the roadmap ("User and Role Management UI") is to implement the **Role Management** functionality. This will be done in parts.

**Plan for this Turn: Role Management UI - Part 1 (Role Listing and Basic CRUD Dialog for Name/Description)**

**Objective:**
1.  Define Data Transfer Objects (DTOs) for creating and updating roles.
2.  Extend `SecurityManager` with methods for CRUD operations on roles (name/description only for now).
3.  Create a `RoleManagementWidget` to list roles and provide basic actions (Add, Edit, Delete).
4.  Create a `RoleTableModel` for the list view.
5.  Create a `RoleDialog` for adding/editing a role's name and description. Permission assignment within this dialog will be deferred to a later part.
6.  Integrate the `RoleManagementWidget` into a new "Roles" tab within the `SettingsWidget`.

**Execution Plan:**

**I. Data Transfer Objects (`app/utils/pydantic_models.py`)**

1.  Define `RoleCreateData(AppBaseModel)`:
    *   Fields: `name: str = Field(..., min_length=3, max_length=50)`, `description: Optional[str] = Field(None, max_length=200)`.
2.  Define `RoleUpdateData(RoleCreateData)`:
    *   Fields: `id: int` (inherited fields: `name`, `description`).
3.  Define `PermissionData(AppBaseModel)` (for future use in RoleDialog Part 2, but good to define now):
    *   Fields: `id: int`, `code: str`, `description: Optional[str] = None`, `module: str`.
    *   **Checklist**: [X] `RoleCreateData` defined. [X] `RoleUpdateData` defined. [X] `PermissionData` defined.

**II. `SecurityManager` Enhancements (`app/core/security_manager.py`)**

1.  Add `async def get_role_by_id(self, role_id: int) -> Optional[Role]`: Fetch `Role` ORM by ID.
2.  Add `async def create_role(self, dto: RoleCreateData, current_admin_user_id: int) -> Result[Role]`:
    *   Check for role name uniqueness.
    *   Create and save new `Role` ORM.
3.  Add `async def update_role(self, dto: RoleUpdateData, current_admin_user_id: int) -> Result[Role]`:
    *   Fetch role. Prevent editing "Administrator" role name.
    *   If name changed, check for uniqueness.
    *   Update name/description. Save.
4.  Add `async def delete_role(self, role_id: int, current_admin_user_id: int) -> Result[None]`:
    *   Prevent deletion of "Administrator" role.
    *   Check if role is assigned to any users (query `core.user_roles`). If so, return failure (user reassignment is complex, defer).
    *   If safe to delete, delete the role. (Associated `role_permissions` should cascade delete due to DB schema).
5.  Add `async def get_all_permissions(self) -> List[Permission]`: Fetch all `Permission` ORM objects (for RoleDialog Part 2).
    *   **Checklist**: [X] `get_role_by_id` added. [X] `create_role` added. [X] `update_role` added. [X] `delete_role` added (with basic safety checks). [X] `get_all_permissions` added.

**III. UI Files for Role Management**

1.  **Create `app/ui/settings/role_table_model.py` (New File)**:
    *   `RoleTableModel(QAbstractTableModel)`.
    *   Input: `List[RoleData]`.
    *   Headers: "ID", "Name", "Description".
    *   Implement `rowCount`, `columnCount`, `headerData`, `data`.
    *   Helper `get_role_id_at_row()`.
    *   **Checklist**: [X] Model class created. [X] Displays `RoleData`. [X] Helper method present.

2.  **Create `app/ui/settings/role_dialog.py` (New File - Part 1: Name/Description only)**:
    *   `RoleDialog(QDialog)`.
    *   Constructor: `__init__(app_core, current_admin_user_id, role_id_to_edit=None, parent=None)`.
    *   UI: `QLineEdit` for Name, `QTextEdit` (or `QLineEdit`) for Description.
    *   Logic: Load existing role for edit. `_collect_data()` to create `RoleCreateData`/`RoleUpdateData`. `_perform_save()` calls `SecurityManager`. Emit `role_saved` signal.
    *   Placeholder for permission assignment UI (e.g., a `QLabel("Permission assignment will be here.")`).
    *   **Checklist**: [X] Dialog class created. [X] Name/Description fields present. [X] Loads existing role. [X] Collects data to DTO. [X] Saves via manager. [X] Emits signal.

3.  **Create `app/ui/settings/role_management_widget.py` (New File)**:
    *   `RoleManagementWidget(QWidget)`.
    *   UI: Toolbar (Add, Edit, Delete - Delete might be initially disabled if complex checks are deferred). `QTableView` using `RoleTableModel`.
    *   Logic: `_load_roles()` calls `SecurityManager.get_all_roles()` (maps to `RoleData` DTOs for model).
    *   Action slots launch `RoleDialog`. `_update_action_states()` for toolbar.
    *   `_on_delete_role()`: Confirm, then call `SecurityManager.delete_role()`. Refresh list on success.
    *   **Checklist**: [X] Widget class created. [X] UI elements present. [X] Roles load and display. [X] Add/Edit actions launch dialog. [X] Delete action calls manager. [X] List refreshes after CUD.

4.  **Update `app/ui/settings/settings_widget.py`**:
    *   Import `RoleManagementWidget`.
    *   Instantiate `RoleManagementWidget`.
    *   Add a new "Roles & Permissions" tab (or just "Roles" for now) to its `QTabWidget` and add `RoleManagementWidget` to it.
    *   **Checklist**: [X] Import added. [X] New tab added with `RoleManagementWidget`.

5.  **Update `app/ui/settings/__init__.py`**:
    *   Export `RoleManagementWidget`, `RoleTableModel`, `RoleDialog`.
    *   **Checklist**: [X] Exports added.

This plan provides a solid foundation for role management. Permission assignment UI will be a subsequent step for this module.

I will now generate the new and updated files.

---
**1. Update `app/utils/pydantic_models.py`**
```python
# app/utils/pydantic_models.py
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
class RoleData(AppBaseModel): # Already existed, confirmed structure
    id: int
    name: str
    description: Optional[str] = None

class UserSummaryData(AppBaseModel): # Already existed, confirmed structure
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool
    last_login: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list) 

class UserRoleAssignmentData(AppBaseModel): # Already existed, confirmed structure
    role_id: int

class UserBaseData(AppBaseModel): # Already existed, confirmed structure
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    is_active: bool = True

class UserCreateInternalData(UserBaseData): # Already existed, confirmed structure
    password_hash: str 
    assigned_roles: List[UserRoleAssignmentData] = Field(default_factory=list)

class UserCreateData(UserBaseData, UserAuditData): # Already existed, confirmed structure
    password: str = Field(..., min_length=8)
    confirm_password: str
    assigned_role_ids: List[int] = Field(default_factory=list)

    @root_validator(skip_on_failure=True)
    def passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('password'), values.get('confirm_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('Passwords do not match')
        return values

class UserUpdateData(UserBaseData, UserAuditData): # Already existed, confirmed structure
    id: int
    assigned_role_ids: List[int] = Field(default_factory=list)

class UserPasswordChangeData(AppBaseModel, UserAuditData): # Already existed, confirmed structure
    user_id_to_change: int 
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    @root_validator(skip_on_failure=True)
    def new_passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('new_password'), values.get('confirm_new_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('New passwords do not match')
        return values

# --- NEW DTOs for Role Management ---
class RoleCreateData(AppBaseModel): # No UserAuditData, roles are system-level
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    # permission_codes: List[str] = Field(default_factory=list) # For Part 2

class RoleUpdateData(RoleCreateData):
    id: int
    # permission_codes: List[str] = Field(default_factory=list) # For Part 2

class PermissionData(AppBaseModel): # For listing available permissions
    id: int
    code: str
    description: Optional[str] = None
    module: str

```

---
**2. Update `app/core/security_manager.py`**
```python
# File: app/core/security_manager.py
import bcrypt
from typing import Optional, List, cast
from app.models.core.user import User, Role, Permission 
from app.models.accounting.account import Account 
from sqlalchemy import select, update, delete 
from sqlalchemy.orm import selectinload, joinedload
from app.core.database_manager import DatabaseManager 
import datetime 
from app.utils.result import Result
from app.utils.pydantic_models import (
    UserSummaryData, UserCreateInternalData, UserRoleAssignmentData,
    UserCreateData, UserUpdateData, UserPasswordChangeData,
    RoleCreateData, RoleUpdateData, PermissionData # New DTOs for Roles/Permissions
)


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
            stmt = select(Role).options(selectinload(Role.permissions)).order_by(Role.name) # Eager load permissions
            result = await session.execute(stmt)
            return list(result.scalars().unique().all()) # unique() because of join with permissions

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

    # --- New Role Management Methods ---
    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        async with self.db_manager.session() as session:
            # Eager load permissions when fetching a single role for editing
            stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def create_role(self, dto: RoleCreateData, current_admin_user_id: int) -> Result[Role]:
        async with self.db_manager.session() as session:
            stmt_exist = select(Role).where(Role.name == dto.name)
            if (await session.execute(stmt_exist)).scalars().first():
                return Result.failure([f"Role name '{dto.name}' already exists."])
            
            new_role = Role(name=dto.name, description=dto.description)
            # created_at, updated_at are handled by TimestampMixin in Role model
            
            session.add(new_role)
            await session.flush()
            await session.refresh(new_role)
            return Result.success(new_role)

    async def update_role(self, dto: RoleUpdateData, current_admin_user_id: int) -> Result[Role]:
        async with self.db_manager.session() as session:
            role_to_update = await session.get(Role, dto.id)
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
            role_to_update.updated_at = datetime.datetime.now(datetime.timezone.utc) # Manually if TimestampMixin not used
            
            await session.flush()
            await session.refresh(role_to_update)
            return Result.success(role_to_update)

    async def delete_role(self, role_id: int, current_admin_user_id: int) -> Result[None]:
        async with self.db_manager.session() as session:
            role_to_delete = await session.get(Role, role_id, options=[selectinload(Role.users)])
            if not role_to_delete:
                return Result.failure([f"Role with ID {role_id} not found."])

            if role_to_delete.name == "Administrator":
                return Result.failure(["The 'Administrator' role cannot be deleted."])
            
            if role_to_delete.users: # Check if role is assigned to any users
                user_list = ", ".join([user.username for user in role_to_delete.users[:5]])
                if len(role_to_delete.users) > 5: user_list += "..."
                return Result.failure([f"Role '{role_to_delete.name}' is assigned to users ({user_list}) and cannot be deleted. Please reassign users first."])
            
            # Permissions associated via role_permissions table will be cascade deleted by DB if FK is set up correctly.
            await session.delete(role_to_delete)
            await session.flush() # Make sure delete is processed
            return Result.success(None)

    async def get_all_permissions(self) -> List[PermissionData]:
        async with self.db_manager.session() as session:
            stmt = select(Permission).order_by(Permission.module, Permission.code)
            result = await session.execute(stmt)
            permissions_orm = result.scalars().all()
            return [PermissionData.model_validate(p) for p in permissions_orm]
            
    async def assign_permissions_to_role(self, role_id: int, permission_ids: List[int], current_admin_user_id: int) -> Result[Role]:
        async with self.db_manager.session() as session:
            role = await session.get(Role, role_id, options=[selectinload(Role.permissions)])
            if not role:
                return Result.failure([f"Role with ID {role_id} not found."])
            
            if role.name == "Administrator":
                return Result.failure(["Permissions for 'Administrator' role cannot be changed from UI; it has all permissions implicitly."])

            new_permissions_orm: List[Permission] = []
            if permission_ids:
                perm_q = await session.execute(select(Permission).where(Permission.id.in_(permission_ids))) # type: ignore
                new_permissions_orm = list(perm_q.scalars().all())
                if len(new_permissions_orm) != len(set(permission_ids)):
                     return Result.failure(["One or more selected permission IDs are invalid."])
            
            role.permissions.clear()
            for perm in new_permissions_orm:
                role.permissions.append(perm)
            
            role.updated_at = datetime.datetime.now(datetime.timezone.utc)
            await session.flush()
            await session.refresh(role)
            await session.refresh(role, attribute_names=['permissions'])
            return Result.success(role)

```

---
**3. Create `app/ui/settings/role_table_model.py` (New File)**
```python
# app/ui/settings/role_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any

from app.utils.pydantic_models import RoleData # Use RoleData DTO

class RoleTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[RoleData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Name", "Description"]
        self._data: List[RoleData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        
        row = index.row(); col = index.column()
        if not (0 <= row < len(self._data)): return None
            
        role_data: RoleData = self._data[row]

        if col == 0: return str(role_data.id)
        if col == 1: return role_data.name
        if col == 2: return role_data.description or ""
            
        return None

    def get_role_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            return self._data[row].id 
        return None
        
    def get_role_name_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].name
        return None

    def update_data(self, new_data: List[RoleData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

---
**4. Create `app/ui/settings/role_dialog.py` (New File - Part 1)**
```python
# app/ui/settings/role_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QLabel, QTextEdit
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import RoleCreateData, RoleUpdateData, RoleData
from app.models.core.user import Role # ORM for loading
from app.utils.result import Result
from app.utils.json_helpers import json_converter

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class RoleDialog(QDialog):
    role_saved = Signal(int) # Emits role ID

    def __init__(self, app_core: ApplicationCore, 
                 current_admin_user_id: int, 
                 role_id_to_edit: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_admin_user_id = current_admin_user_id
        self.role_id_to_edit = role_id_to_edit
        self.loaded_role_orm: Optional[Role] = None

        self.is_new_role = self.role_id_to_edit is None
        self.setWindowTitle("Add New Role" if self.is_new_role else "Edit Role")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        if self.role_id_to_edit:
            QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_existing_role_data()))
        else:
            self.name_edit.setFocus() # Focus on name for new role

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter role name (e.g., Sales Manager)")
        form_layout.addRow("Role Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter a brief description for this role.")
        self.description_edit.setFixedHeight(80)
        form_layout.addRow("Description:", self.description_edit)
        
        # Placeholder for Permission Assignment UI (Part 2)
        self.permissions_placeholder_label = QLabel(
            "<i>Permission assignment will be available here in a future update.</i>"
        )
        self.permissions_placeholder_label.setTextFormat(Qt.TextFormat.RichText)
        self.permissions_placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.permissions_placeholder_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        form_layout.addRow(self.permissions_placeholder_label)


        main_layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)
        
    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save)
        self.button_box.rejected.connect(self.reject)

    async def _load_existing_role_data(self):
        if not self.role_id_to_edit or not self.app_core.security_manager: return

        self.loaded_role_orm = await self.app_core.security_manager.get_role_by_id(self.role_id_to_edit)
        if self.loaded_role_orm:
            role_dict = {
                "id": self.loaded_role_orm.id,
                "name": self.loaded_role_orm.name,
                "description": self.loaded_role_orm.description
            }
            role_json_str = json.dumps(role_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, role_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Role ID {self.role_id_to_edit} not found.")
            self.reject()

    @Slot(str)
    def _populate_fields_slot(self, role_json_str: str):
        try:
            role_data = json.loads(role_json_str) 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse role data for editing."); return

        self.name_edit.setText(role_data.get("name", ""))
        self.description_edit.setText(role_data.get("description", "") or "")

        # Prevent editing name of "Administrator" role
        if role_data.get("name") == "Administrator":
            self.name_edit.setReadOnly(True)
            self.name_edit.setToolTip("The 'Administrator' role name cannot be changed.")

    def _collect_data(self) -> Optional[Union[RoleCreateData, RoleUpdateData]]:
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip() or None
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Role Name is required.")
            return None
        
        try:
            if self.is_new_role:
                return RoleCreateData(name=name, description=description)
            else:
                assert self.role_id_to_edit is not None
                return RoleUpdateData(id=self.role_id_to_edit, name=name, description=description)
        except ValueError as pydantic_error: # Catches Pydantic validation errors
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
            return None

    @Slot()
    def on_save(self):
        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button: ok_button.setEnabled(False)
            
            future = schedule_task_from_qt(self._perform_save(dto))
            if future:
                future.add_done_callback(
                    lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
                )
            else: # Handle scheduling failure
                if ok_button: ok_button.setEnabled(True)

    async def _perform_save(self, dto: Union[RoleCreateData, RoleUpdateData]):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Security Manager not available."))
            return

        result: Result[Role]
        action_verb_present = "update" if isinstance(dto, RoleUpdateData) else "create"
        action_verb_past = "updated" if isinstance(dto, RoleUpdateData) else "created"

        if isinstance(dto, RoleUpdateData):
            result = await self.app_core.security_manager.update_role(dto, self.current_admin_user_id)
        else: # RoleCreateData
            result = await self.app_core.security_manager.create_role(dto, self.current_admin_user_id)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self.parentWidget() if self.parentWidget() else self), 
                Q_ARG(str, "Success"), 
                Q_ARG(str, f"Role '{result.value.name}' {action_verb_past} successfully."))
            self.role_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to {action_verb_present} role:\n{', '.join(result.errors)}"))

```

---
**5. Create `app/ui/settings/role_management_widget.py` (New File)**
```python
# app/ui/settings/role_management_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QPushButton, QToolBar, 
    QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.settings.role_table_model import RoleTableModel
from app.ui.settings.role_dialog import RoleDialog
from app.utils.pydantic_models import RoleData
from app.utils.json_helpers import json_converter
from app.utils.result import Result
from app.models.core.user import Role # For ORM type hint from SecurityManager

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class RoleManagementWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass 
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_roles()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self.roles_table = QTableView()
        self.roles_table.setAlternatingRowColors(True)
        self.roles_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.roles_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.roles_table.horizontalHeader().setStretchLastSection(True) 
        self.roles_table.setSortingEnabled(True)
        self.roles_table.doubleClicked.connect(self._on_edit_role_double_click)

        self.table_model = RoleTableModel()
        self.roles_table.setModel(self.table_model)
        
        header = self.roles_table.horizontalHeader()
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.roles_table.setColumnHidden(id_col_idx, True)
        
        header.setSectionResizeMode(self.table_model._headers.index("Name"), QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.table_model._headers.index("Description"), QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.roles_table)
        self.setLayout(self.main_layout)

        if self.roles_table.selectionModel():
            self.roles_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Role Management Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Role", self)
        self.toolbar_add_action.triggered.connect(self._on_add_role)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Role", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_role)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_delete_action = QAction(QIcon(self.icon_path_prefix + "remove.svg"), "Delete Role", self)
        self.toolbar_delete_action.triggered.connect(self._on_delete_role)
        self.toolbar.addAction(self.toolbar_delete_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_roles()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _update_action_states(self):
        selected_rows = self.roles_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_modify = False
        is_admin_role_selected = False

        if single_selection:
            can_modify = True
            row_idx = selected_rows[0].row()
            role_name = self.table_model.get_role_name_at_row(row_idx)
            if role_name == "Administrator":
                is_admin_role_selected = True
        
        self.toolbar_edit_action.setEnabled(can_modify) # Admin role description can be edited
        self.toolbar_delete_action.setEnabled(can_modify and not is_admin_role_selected)

    async def _load_roles(self):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Security Manager not available."))
            return
        try:
            roles_orm: List[Role] = await self.app_core.security_manager.get_all_roles()
            roles_dto: List[RoleData] = [RoleData.model_validate(r) for r in roles_orm]
            json_data = json.dumps([r.model_dump() for r in roles_dto], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e:
            self.app_core.logger.error(f"Unexpected error loading roles: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading roles: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str) 
            role_dtos: List[RoleData] = [RoleData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(role_dtos)
        except Exception as e: 
            self.app_core.logger.error(f"Failed to parse/validate role data for table: {e}", exc_info=True)
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate role data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_role(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_role_id(self) -> Optional[int]:
        selected_rows = self.roles_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None
        return self.table_model.get_role_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_role(self):
        role_id = self._get_selected_role_id()
        if role_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single role to edit.")
            return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, role_id_to_edit=role_id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot(QModelIndex)
    def _on_edit_role_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        role_id = self.table_model.get_role_id_at_row(index.row())
        if role_id is None: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, role_id_to_edit=role_id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_delete_role(self):
        role_id = self._get_selected_role_id()
        if role_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single role to delete.")
            return
        
        role_name = self.table_model.get_role_name_at_row(self.roles_table.currentIndex().row())
        if role_name == "Administrator":
            QMessageBox.warning(self, "Action Denied", "The 'Administrator' role cannot be deleted.")
            return

        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete the role '{role_name}' (ID: {role_id})?\nThis action cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.security_manager.delete_role(role_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_delete_role_result)
        else: self._handle_delete_role_result(None)

    def _handle_delete_role_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule role deletion."); return
        try:
            result: Result[None] = future.result()
            if result.is_success:
                QMessageBox.information(self, "Success", "Role deleted successfully.")
                schedule_task_from_qt(self._load_roles()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete role:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling role deletion result: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during role deletion: {str(e)}")
        finally:
            self._update_action_states() # Ensure actions are re-evaluated

    @Slot(int)
    def _refresh_list_after_save(self, role_id: int):
        self.app_core.logger.info(f"RoleDialog reported save for Role ID: {role_id}. Refreshing role list.")
        schedule_task_from_qt(self._load_roles())

```

---
**5. Update `app/ui/settings/settings_widget.py`** (This remains the same as generated in the previous response, as the changes there were to add the "Users" tab. Now we are adding a "Roles" tab.)
```python
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView,
                               QHBoxLayout, QTabWidget 
                               ) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt, QAbstractTableModel, QModelIndex 
from PySide6.QtGui import QColor, QFont 
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData, FiscalYearCreateData, FiscalYearData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from app.models.accounting.fiscal_year import FiscalYear 
from app.ui.accounting.fiscal_year_dialog import FiscalYearDialog 
from app.ui.settings.user_management_widget import UserManagementWidget 
from app.ui.settings.role_management_widget import RoleManagementWidget # New Import
from decimal import Decimal, InvalidOperation
import asyncio
import json 
from typing import Optional, List, Any, Dict 
from app.main import schedule_task_from_qt 
from datetime import date as python_date, datetime 
from app.utils.json_helpers import json_converter, json_date_hook 

class FiscalYearTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[FiscalYearData]] = None, parent=None): 
        super().__init__(parent)
        self._headers = ["Name", "Start Date", "End Date", "Status"]
        self._data: List[FiscalYearData] = data or []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): # Removed "or role != Qt.ItemDataRole.DisplayRole" to allow FontRole etc.
            return None
        
        try:
            fy = self._data[index.row()]
            column = index.column()

            if role == Qt.ItemDataRole.DisplayRole:
                if column == 0: return fy.year_name
                if column == 1: return fy.start_date.strftime('%d/%m/%Y') if isinstance(fy.start_date, python_date) else str(fy.start_date)
                if column == 2: return fy.end_date.strftime('%d/%m/%Y') if isinstance(fy.end_date, python_date) else str(fy.end_date)
                if column == 3: return "Closed" if fy.is_closed else "Open"
            elif role == Qt.ItemDataRole.FontRole:
                if column == 3: 
                    font = QFont()
                    if fy.is_closed:
                        pass 
                    else: 
                        font.setBold(True)
                    return font
            elif role == Qt.ItemDataRole.ForegroundRole:
                 if column == 3 and not fy.is_closed: 
                    return QColor("green")
        except IndexError:
            return None 
        return None

    def get_fiscal_year_at_row(self, row: int) -> Optional[FiscalYearData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
        
    def update_data(self, new_data: List[FiscalYearData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._loaded_settings_obj: Optional[CompanySetting] = None 
        
        self.main_layout = QVBoxLayout(self) 
        self.tab_widget = QTabWidget() 
        self.main_layout.addWidget(self.tab_widget)

        # --- Company Settings Tab ---
        self.company_settings_tab = QWidget()
        company_tab_layout = QVBoxLayout(self.company_settings_tab) 

        company_settings_group = QGroupBox("Company Information")
        company_settings_form_layout = QFormLayout(company_settings_group) 

        self.company_name_edit = QLineEdit()
        self.legal_name_edit = QLineEdit()
        self.uen_edit = QLineEdit()
        self.gst_reg_edit = QLineEdit()
        self.gst_registered_check = QCheckBox("GST Registered")
        self.base_currency_combo = QComboBox() 
        self.address_line1_edit = QLineEdit()
        self.address_line2_edit = QLineEdit()
        self.postal_code_edit = QLineEdit()
        self.city_edit = QLineEdit()
        self.country_edit = QLineEdit()
        self.contact_person_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.website_edit = QLineEdit()
        self.fiscal_year_start_month_spin = QSpinBox()
        self.fiscal_year_start_month_spin.setRange(1, 12)
        self.fiscal_year_start_day_spin = QSpinBox()
        self.fiscal_year_start_day_spin.setRange(1,31)
        self.tax_id_label_edit = QLineEdit()
        self.date_format_combo = QComboBox() 
        self.date_format_combo.addItems(["dd/MM/yyyy", "yyyy-MM-dd", "MM/dd/yyyy"])

        company_settings_form_layout.addRow("Company Name*:", self.company_name_edit)
        company_settings_form_layout.addRow("Legal Name:", self.legal_name_edit)
        company_settings_form_layout.addRow("UEN No:", self.uen_edit)
        company_settings_form_layout.addRow("GST Reg. No:", self.gst_reg_edit)
        company_settings_form_layout.addRow(self.gst_registered_check)
        company_settings_form_layout.addRow("Base Currency:", self.base_currency_combo)
        company_settings_form_layout.addRow("Address Line 1:", self.address_line1_edit)
        company_settings_form_layout.addRow("Address Line 2:", self.address_line2_edit)
        company_settings_form_layout.addRow("Postal Code:", self.postal_code_edit)
        company_settings_form_layout.addRow("City:", self.city_edit)
        company_settings_form_layout.addRow("Country:", self.country_edit)
        company_settings_form_layout.addRow("Contact Person:", self.contact_person_edit)
        company_settings_form_layout.addRow("Phone:", self.phone_edit)
        company_settings_form_layout.addRow("Email:", self.email_edit)
        company_settings_form_layout.addRow("Website:", self.website_edit)
        company_settings_form_layout.addRow("Fiscal Year Start Month:", self.fiscal_year_start_month_spin)
        company_settings_form_layout.addRow("Fiscal Year Start Day:", self.fiscal_year_start_day_spin)
        company_settings_form_layout.addRow("Tax ID Label:", self.tax_id_label_edit)
        company_settings_form_layout.addRow("Date Format:", self.date_format_combo)
        
        self.save_company_settings_button = QPushButton("Save Company Settings")
        self.save_company_settings_button.clicked.connect(self.on_save_company_settings)
        company_settings_form_layout.addRow(self.save_company_settings_button)
        
        company_tab_layout.addWidget(company_settings_group)
        company_tab_layout.addStretch() 
        self.tab_widget.addTab(self.company_settings_tab, "Company")

        # --- Fiscal Year Management Tab ---
        self.fiscal_year_tab = QWidget()
        fiscal_tab_main_layout = QVBoxLayout(self.fiscal_year_tab)
        
        fiscal_year_group = QGroupBox("Fiscal Year Management")
        fiscal_year_group_layout = QVBoxLayout(fiscal_year_group) 

        self.fiscal_years_table = QTableView()
        self.fiscal_years_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fiscal_years_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.fiscal_years_table.horizontalHeader().setStretchLastSection(True)
        self.fiscal_years_table.setMinimumHeight(150) 
        self.fiscal_year_model = FiscalYearTableModel() 
        self.fiscal_years_table.setModel(self.fiscal_year_model)
        fiscal_year_group_layout.addWidget(self.fiscal_years_table)

        fy_button_layout = QHBoxLayout() 
        self.add_fy_button = QPushButton("Add New Fiscal Year...")
        self.add_fy_button.clicked.connect(self.on_add_fiscal_year)
        fy_button_layout.addWidget(self.add_fy_button)
        fy_button_layout.addStretch()
        fiscal_year_group_layout.addLayout(fy_button_layout)
        
        fiscal_tab_main_layout.addWidget(fiscal_year_group)
        fiscal_tab_main_layout.addStretch() 
        self.tab_widget.addTab(self.fiscal_year_tab, "Fiscal Years")

        # --- User Management Tab ---
        self.user_management_widget = UserManagementWidget(self.app_core)
        self.tab_widget.addTab(self.user_management_widget, "Users")

        # --- Role Management Tab (NEW) ---
        self.role_management_widget = RoleManagementWidget(self.app_core)
        self.tab_widget.addTab(self.role_management_widget, "Roles & Permissions")
        
        self.setLayout(self.main_layout) 

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_initial_data()))

    async def load_initial_data(self):
        await self.load_company_settings()
        await self._load_fiscal_years() 

    async def load_company_settings(self):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        
        currencies_loaded_successfully = False
        active_currencies_data: List[Dict[str, str]] = [] 
        if self.app_core.currency_manager:
            try:
                active_currencies_orm: List[Currency] = await self.app_core.currency_manager.get_active_currencies()
                for curr in active_currencies_orm:
                    active_currencies_data.append({"code": curr.code, "name": curr.name})
                QMetaObject.invokeMethod(self, "_populate_currency_combo_slot", Qt.ConnectionType.QueuedConnection, 
                                         Q_ARG(str, json.dumps(active_currencies_data)))
                currencies_loaded_successfully = True
            except Exception as e:
                error_msg = f"Error loading currencies for settings: {e}"
                self.app_core.logger.error(error_msg, exc_info=True) 
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Currency Load Error"), Q_ARG(str, error_msg))
        
        if not currencies_loaded_successfully: 
            QMetaObject.invokeMethod(self.base_currency_combo, "addItems", Qt.ConnectionType.QueuedConnection, Q_ARG(list, ["SGD", "USD"]))

        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        self._loaded_settings_obj = settings_obj 
        
        settings_data_for_ui_json: Optional[str] = None
        if settings_obj:
            settings_dict = { col.name: getattr(settings_obj, col.name) for col in CompanySetting.__table__.columns }
            settings_data_for_ui_json = json.dumps(settings_dict, default=json_converter)
        
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, settings_data_for_ui_json if settings_data_for_ui_json else ""))

    @Slot(str) 
    def _populate_currency_combo_slot(self, currencies_json_str: str): 
        try: currencies_data: List[Dict[str,str]] = json.loads(currencies_json_str)
        except json.JSONDecodeError: currencies_data = [{"code": "SGD", "name": "Singapore Dollar"}] 
            
        current_selection = self.base_currency_combo.currentData()
        self.base_currency_combo.clear()
        if currencies_data: 
            for curr_data in currencies_data: self.base_currency_combo.addItem(f"{curr_data['code']} - {curr_data['name']}", curr_data['code']) 
        
        target_currency_code = current_selection
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj and self._loaded_settings_obj.base_currency:
            target_currency_code = self._loaded_settings_obj.base_currency
        
        if target_currency_code:
            idx = self.base_currency_combo.findData(target_currency_code) 
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
            else: 
                idx_sgd = self.base_currency_combo.findData("SGD") 
                if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        elif self.base_currency_combo.count() > 0: self.base_currency_combo.setCurrentIndex(0)

    @Slot(str) 
    def _update_ui_from_settings_slot(self, settings_json_str: str):
        settings_data: Optional[Dict[str, Any]] = None
        if settings_json_str:
            try:
                settings_data = json.loads(settings_json_str, object_hook=json_date_hook)
            except json.JSONDecodeError: 
                QMessageBox.critical(self, "Error", "Failed to parse settings data."); settings_data = None

        if settings_data:
            self.company_name_edit.setText(settings_data.get("company_name", ""))
            self.legal_name_edit.setText(settings_data.get("legal_name", "") or "")
            self.uen_edit.setText(settings_data.get("uen_no", "") or "")
            self.gst_reg_edit.setText(settings_data.get("gst_registration_no", "") or "")
            self.gst_registered_check.setChecked(settings_data.get("gst_registered", False))
            self.address_line1_edit.setText(settings_data.get("address_line1", "") or "")
            self.address_line2_edit.setText(settings_data.get("address_line2", "") or "")
            self.postal_code_edit.setText(settings_data.get("postal_code", "") or "")
            self.city_edit.setText(settings_data.get("city", "Singapore") or "Singapore")
            self.country_edit.setText(settings_data.get("country", "Singapore") or "Singapore")
            self.contact_person_edit.setText(settings_data.get("contact_person", "") or "")
            self.phone_edit.setText(settings_data.get("phone", "") or "")
            self.email_edit.setText(settings_data.get("email", "") or "")
            self.website_edit.setText(settings_data.get("website", "") or "")
            self.fiscal_year_start_month_spin.setValue(settings_data.get("fiscal_year_start_month", 1))
            self.fiscal_year_start_day_spin.setValue(settings_data.get("fiscal_year_start_day", 1))
            self.tax_id_label_edit.setText(settings_data.get("tax_id_label", "UEN") or "UEN")
            
            date_fmt = settings_data.get("date_format", "dd/MM/yyyy") 
            date_fmt_idx = self.date_format_combo.findText(date_fmt, Qt.MatchFlag.MatchFixedString)
            if date_fmt_idx != -1: self.date_format_combo.setCurrentIndex(date_fmt_idx)
            else: self.date_format_combo.setCurrentIndex(0) 

            if self.base_currency_combo.count() > 0: 
                base_currency = settings_data.get("base_currency")
                if base_currency:
                    idx = self.base_currency_combo.findData(base_currency) 
                    if idx != -1: 
                        self.base_currency_combo.setCurrentIndex(idx)
                    else: 
                        idx_sgd = self.base_currency_combo.findData("SGD")
                        if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        else:
            if not self._loaded_settings_obj : 
                 QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")

    @Slot()
    def on_save_company_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return
        selected_currency_code = self.base_currency_combo.currentData() or "SGD"
        dto = CompanySettingData(
            id=1, 
            company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None, uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None, gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            address_line1=self.address_line1_edit.text() or None, address_line2=self.address_line2_edit.text() or None,
            postal_code=self.postal_code_edit.text() or None, city=self.city_edit.text() or "Singapore",
            country=self.country_edit.text() or "Singapore", contact_person=self.contact_person_edit.text() or None,
            phone=self.phone_edit.text() or None, email=self.email_edit.text() or None, 
            website=self.website_edit.text() or None,
            fiscal_year_start_month=self.fiscal_year_start_month_spin.value(), 
            fiscal_year_start_day=self.fiscal_year_start_day_spin.value(),  
            base_currency=selected_currency_code, 
            tax_id_label=self.tax_id_label_edit.text() or "UEN",       
            date_format=self.date_format_combo.currentText() or "dd/MM/yyyy", 
            logo=None 
        )
        schedule_task_from_qt(self.perform_save_company_settings(dto))

    async def perform_save_company_settings(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            update_dict = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            for field_name, field_value in update_dict.items():
                if hasattr(orm_obj_to_save, field_name): 
                    if field_name == 'email' and field_value is not None: 
                        setattr(orm_obj_to_save, field_name, str(field_value))
                    else:
                        setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            if 'email' in dict_data and dict_data['email'] is not None: dict_data['email'] = str(dict_data['email'])
            orm_obj_to_save = CompanySetting(**dict_data) # type: ignore
            if settings_data.id: orm_obj_to_save.id = settings_data.id 
        
        if self.app_core.current_user: orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 
        result_orm = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        message_title = "Success" if result_orm else "Error"
        message_text = "Company settings saved successfully." if result_orm else "Failed to save company settings."
        msg_box_method = QMessageBox.information if result_orm else QMessageBox.warning
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, message_title), Q_ARG(str, message_text))

    async def _load_fiscal_years(self):
        if not self.app_core.fiscal_period_manager:
            self.app_core.logger.error("FiscalPeriodManager not available in SettingsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Service Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return
        try:
            fy_orms: List[FiscalYear] = await self.app_core.fiscal_period_manager.get_all_fiscal_years()
            fy_dtos_for_table: List[FiscalYearData] = []
            for fy_orm in fy_orms:
                fy_dtos_for_table.append(FiscalYearData(
                    id=fy_orm.id, year_name=fy_orm.year_name, start_date=fy_orm.start_date,
                    end_date=fy_orm.end_date, is_closed=fy_orm.is_closed, closed_date=fy_orm.closed_date,
                    periods=[] 
                ))
            
            fy_json_data = json.dumps([dto.model_dump(mode='json') for dto in fy_dtos_for_table])
            QMetaObject.invokeMethod(self, "_update_fiscal_years_table_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, fy_json_data))
        except Exception as e:
            error_msg = f"Error loading fiscal years: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Fiscal Year Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_fiscal_years_table_slot(self, fy_json_list_str: str):
        try:
            fy_dict_list = json.loads(fy_json_list_str, object_hook=json_date_hook) 
            fy_dtos: List[FiscalYearData] = [FiscalYearData.model_validate(item_dict) for item_dict in fy_dict_list]
            self.fiscal_year_model.update_data(fy_dtos)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse fiscal year data: {e}")
        except Exception as e_val: 
            QMessageBox.critical(self, "Data Error", f"Invalid fiscal year data format: {e_val}")

    @Slot()
    def on_add_fiscal_year(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        
        dialog = FiscalYearDialog(self.app_core, self.app_core.current_user.id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fy_create_data = dialog.get_fiscal_year_data()
            if fy_create_data:
                schedule_task_from_qt(self._perform_add_fiscal_year(fy_create_data))

    async def _perform_add_fiscal_year(self, fy_data: FiscalYearCreateData):
        if not self.app_core.fiscal_period_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return

        result: Result[FiscalYear] = await self.app_core.fiscal_period_manager.create_fiscal_year_and_periods(fy_data)

        if result.is_success:
            assert result.value is not None
            msg = f"Fiscal Year '{result.value.year_name}' created successfully."
            if fy_data.auto_generate_periods:
                msg += f" {fy_data.auto_generate_periods} periods generated."
            
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, msg))
            schedule_task_from_qt(self._load_fiscal_years()) 
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Failed to create fiscal year:\n{', '.join(result.errors)}"))

```

---
**6. Update `app/ui/settings/__init__.py`** (This remains the same as generated in the previous response, as it already correctly includes `UserPasswordDialog` if it were to be created in a separate file, but it's part of `user_dialog.py`'s thought process in the previous response. Reconfirming exports for clarity.)
```python
# File: app/ui/settings/__init__.py
from .settings_widget import SettingsWidget
from .user_management_widget import UserManagementWidget 
from .user_table_model import UserTableModel 
from .user_dialog import UserDialog 
from .user_password_dialog import UserPasswordDialog 
from .role_management_widget import RoleManagementWidget # New export
from .role_table_model import RoleTableModel # New export
from .role_dialog import RoleDialog # New export


__all__ = [
    "SettingsWidget",
    "UserManagementWidget", 
    "UserTableModel",       
    "UserDialog", 
    "UserPasswordDialog",
    "RoleManagementWidget", # New export
    "RoleTableModel",       # New export
    "RoleDialog",           # New export
]

```

---
https://drive.google.com/file/d/13hYEwFVHlQaGQ_ws3k3VvmZSWJgP14ep/view?usp=sharing, https://drive.google.com/file/d/18AV-7BrkUwk7kQpr8LFSSHMODP6oFYOs/view?usp=sharing, https://drive.google.com/file/d/18xs17NAMOyJxIIn7YAW5_Hxt_EasmnYe/view?usp=sharing, https://drive.google.com/file/d/19QeRpKKgin37J5wKA6z9wbnCIywmKHXx/view?usp=sharing, https://drive.google.com/file/d/1E_9maYq_-0jngxcKzFVK1WObHkUzXzcn/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221EqAAoEAbBCw8IJfsiko4lSxMlixUIqkw%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1FIkt6wn6Ph29zKa6BjuWg5MymXB3xwBN/view?usp=sharing, https://drive.google.com/file/d/1LcMYtkv9s7XDWf1Z_L0y4Mt2XI-E1ChV/view?usp=sharing, https://drive.google.com/file/d/1MNPYsv6jKlmSA9ka-nthRdxmoGxscNKT/view?usp=sharing, https://drive.google.com/file/d/1OAqRup6_pFNaqSbKhvKZ648LGW_vGNHC/view?usp=sharing, https://drive.google.com/file/d/1XVzr3QcXe8dUm0E1rAGlSEloeiMTusAx/view?usp=sharing, https://drive.google.com/file/d/1YEVuNKs7bEWVD6V-NejsmLXZO4a_Tq6F/view?usp=sharing, https://drive.google.com/file/d/1Yjh1wm8uK13MwHJ8nWWt7fDGt_xUxcfe/view?usp=sharing, https://drive.google.com/file/d/1Z4tCtBnhhgZ9oBxAIVk6Nfh_SMwGNjYX/view?usp=sharing, https://drive.google.com/file/d/1aUkaWoQCRm84Q82zCvXChHy8qlZLIc6r/view?usp=sharing, https://drive.google.com/file/d/1fJ5KRnIXSWh5lggrhch8lCDTMwCz9ixp/view?usp=sharing, https://drive.google.com/file/d/1g0BTPiyYf-TubgZlqVArx3Yf0ScSlKa6/view?usp=sharing, https://drive.google.com/file/d/1hHhfoRDBXO8vzthKpWOjI1vH3ccrCWWk/view?usp=sharing, https://drive.google.com/file/d/1hWa5WsgsdwdIUvsHOHqTzLMD37yAg2yV/view?usp=sharing, https://drive.google.com/file/d/1jEPSW2DlYe3CnFfxcrrxQcS1in-CoZDt/view?usp=sharing, https://drive.google.com/file/d/1knLdNW1a19s2XuSALhNPY4jDAp0YTetr/view?usp=sharing, https://drive.google.com/file/d/1p5dvW05gug-BOoy-YguJARN2LK7ED2Bq/view?usp=sharing, https://drive.google.com/file/d/1sdI2jwTCqouVuonjgOxVkMkeDJb1Luc1/view?usp=sharing, https://drive.google.com/file/d/1yezJl1uC8oDZmnom2iG7Rii5ZcAn4i8N/view?usp=sharing, https://drive.google.com/file/d/1zUWfohK07mrZVPwfjE51rfXlbrSkJWN6/view?usp=sharing

