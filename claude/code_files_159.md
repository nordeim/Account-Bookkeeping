<think>
The application launches successfully. The Sales Invoicing posting UI feedback refinements are integrated.

**Current Project Status Recap:**

*   **Sales Invoicing**:
    *   Backend for Draft Management & Posting (`SalesInvoiceManager`): Complete.
    *   `SalesInvoiceDialog` (Create/Edit Drafts): Complete.
    *   `SalesInvoicesWidget` (List View & Post Action): Complete with refined user feedback.
*   All previously implemented features remain stable.

**Next Step Identification (from Roadmap):**

Roadmap items for "Current Focus / Short-term":
1.  **Sales Invoicing**: Complete UI for listing, viewing, and managing Sales Invoices. Implement posting logic (JE creation). <-- *This is now very close to complete. The "Save & Approve" button in `SalesInvoiceDialog` is still a minor pending item but posting from list view is done.*
2.  **Refine Reporting**: Enhance on-screen display and export options for financial reports. <-- Addressed for BS/PL on-screen display. Further export refinements could be done.
3.  **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions. <-- This is a significant, independent feature that hasn't been started yet.

Given the substantial completion of the Sales Invoicing posting flow, and the recent refinement of BS/PL on-screen display, tackling **"User and Role Management UI"** seems like a good next major step. It's a core system feature often needed early.

The "Save & Approve" button in `SalesInvoiceDialog` could be considered a minor polish item for Sales Invoicing, but a full User/Role Management UI is a more substantial roadmap item. Let's prioritize the larger roadmap item.

**Plan for this Turn: Implement User and Role Management UI - Part 1 (User Management Tab in Settings).**

**Objective:**
Create a new sub-tab within the `SettingsWidget` for "User Management". This tab will initially focus on listing users and allowing actions like Add User, Edit User, and Toggle Active Status. Role assignment will be a subsequent part.

**Detailed Plan & Checklist:**

**I. Backend Preparation (Minor additions to `SecurityManager` and DTOs if needed):**

1.  **DTOs (`app/utils/pydantic_models.py`)**:
    *   [ ] Create `UserSummaryData(AppBaseModel)`: `id`, `username`, `full_name`, `email`, `is_active`, `last_login`.
    *   [ ] Create `UserCreateData(AppBaseModel, UserAuditData)`: `username`, `password`, `confirm_password`, `full_name`, `email`, `is_active`, `role_ids: List[int]`. Include validator for password confirmation.
    *   [ ] Create `UserUpdateData(AppBaseModel, UserAuditData)`: `id`, `username` (optional, if allowed to change), `full_name`, `email`, `is_active`, `role_ids: List[int]`. Password change might be separate.
    *   [ ] Create `RoleData(AppBaseModel)`: `id`, `name`, `description`. (For role selection in user dialogs).

2.  **`SecurityManager` (`app/core/security_manager.py`)**:
    *   [ ] Add `async def get_all_users_summary() -> List[UserSummaryData]`: Fetch all users with key details for listing.
    *   [ ] `create_user` already exists, but its signature might need adjustment to take `UserCreateData` DTO and handle `role_ids`.
    *   [ ] Add `async def update_user(dto: UserUpdateData) -> Result[User]`: Update user details (excluding password for now, role changes).
    *   [ ] Add `async def get_user_by_id_for_edit(user_id: int) -> Optional[User]`: Fetch user with roles for dialog.
    *   [ ] Add `async def toggle_user_active_status(user_id: int, current_user_id: int) -> Result[User]`.
    *   [ ] Add `async def get_all_roles() -> List[Role]`.
    *   [ ] Add `async def change_user_password(user_id: int, new_password: str, current_user_id: int) -> Result[None]`. (Separate action)

**II. UI Implementation (`app/ui/settings/settings_widget.py` and new files):**

1.  **Create `app/ui/settings/user_management_widget.py`**:
    *   [ ] Define `UserManagementWidget(QWidget)`.
    *   [ ] UI: Toolbar (Add, Edit, Toggle Active, Change Password), `QTableView` (`self.users_table`).
    *   [ ] Model: `UserTableModel` (to be created).
    *   [ ] Load users (`_load_users`) using `SecurityManager.get_all_users_summary()`.
    *   [ ] Slots for actions, launching `UserDialog`.
    *   [ ] `_update_action_states` based on selection.

2.  **Create `app/ui/settings/user_table_model.py`**:
    *   [ ] `UserTableModel(QAbstractTableModel)` to display `UserSummaryData`. Columns: Username, Full Name, Email, Active, Last Login.

3.  **Create `app/ui/settings/user_dialog.py`**:
    *   [ ] `UserDialog(QDialog)`.
    *   [ ] Fields for `UserCreateData` / `UserUpdateData` (username, full name, email, active checkbox).
    *   [ ] Password fields (password, confirm password) only for new users or a separate "Change Password" dialog. For edit, password fields should be hidden/disabled or handled differently.
    *   [ ] **Role Assignment**: `QListWidget` with checkboxes or a multi-select widget to assign roles (fetched via `SecurityManager.get_all_roles()`).
    *   [ ] Load existing user data for editing.
    *   [ ] On save, call `SecurityManager.create_user` or `update_user`.

4.  **Update `app/ui/settings/settings_widget.py`**:
    *   [ ] Modify its `QTabWidget` to include "User Management" as a new tab.
    *   [ ] Instantiate and add `UserManagementWidget` to this new tab.

5.  **Update `app/ui/settings/__init__.py`**:
    *   [ ] Export new widget, dialog, model classes.

**Focus for *this* turn (Part 1 of User Management UI):**
Due to the scope, this turn will focus on:
*   DTOs: `UserSummaryData`, `RoleData`. Initial thoughts on `UserCreateData`/`UserUpdateData`.
*   `SecurityManager`: Methods `get_all_users_summary()`, `get_user_by_id_for_edit()`, `toggle_user_active_status()`, `get_all_roles()`.
*   `UserManagementWidget`: Basic structure, table view, toolbar (actions stubbed).
*   `UserTableModel`: To display basic user info.
*   `SettingsWidget`: Add the "User Management" tab and placeholder `UserManagementWidget`.

Creation/Editing of users via `UserDialog` will be Part 2 for User Management.

This breaks down the large "User and Role Management UI" into manageable chunks.
</think>

The application is stable, and the Sales Invoicing functionality (draft management and posting backend) is in a good state. Excellent!

As per the roadmap, the next major feature to tackle is **"User and Role Management UI"**. This is a crucial system feature. We'll start by implementing the User Management part.

**Plan for this Turn: User Management UI - Part 1 (List Users and Basic Actions)**

**Objective:**
1.  Create the necessary Data Transfer Objects (DTOs) for user data presentation and manipulation.
2.  Extend `SecurityManager` with methods to support listing users, fetching user details for editing, toggling active status, and listing roles (for future use in dialogs).
3.  Create a new `UserManagementWidget` to be placed in a new "Users" tab within `SettingsWidget`.
4.  Implement `UserTableModel` to display user summaries in the `UserManagementWidget`.
5.  Set up the basic UI for `UserManagementWidget` including a table view and a toolbar with stubbed actions for Add, Edit, Toggle Active Status, and Change Password.

The actual `UserDialog` for adding/editing users and detailed role assignment will be handled in a subsequent part.

**Execution Plan:**

**I. Data Transfer Objects (`app/utils/pydantic_models.py`)**

1.  Define `RoleData(AppBaseModel)`: For listing roles.
    *   Fields: `id: int`, `name: str`, `description: Optional[str] = None`.
2.  Define `UserSummaryData(AppBaseModel)`: For the user list view.
    *   Fields: `id: int`, `username: str`, `full_name: Optional[str] = None`, `email: Optional[EmailStr] = None`, `is_active: bool`, `last_login: Optional[datetime] = None`, `roles: List[str] = []` (list of role names).
3.  Define basic structures for `UserCreateData` and `UserUpdateData` (full implementation with validators will follow when `UserDialog` is built).
    *   `UserRoleAssignmentData(AppBaseModel)`: `role_id: int`.
    *   `UserBaseData(AppBaseModel)`: `username: str`, `full_name: Optional[str] = None`, `email: Optional[EmailStr] = None`, `is_active: bool = True`.
    *   `UserCreateInternalData(UserBaseData)`: `password: str`, `assigned_roles: List[UserRoleAssignmentData] = []`.
    *   `UserCreateData(UserBaseData)`: `password: str = Field(..., min_length=8)`, `confirm_password: str`, `assigned_role_ids: List[int] = []`. Root validator for password confirmation.
    *   `UserUpdateData(UserBaseData, UserAuditData)`: `id: int`, `assigned_role_ids: List[int] = []`. (Password change handled separately).
    *   **Checklist**: [ ] `RoleData` DTO defined. [ ] `UserSummaryData` DTO defined. [ ] Basic `UserCreateData`/`UserUpdateData` DTOs defined.

**II. `SecurityManager` Enhancements (`app/core/security_manager.py`)**

1.  Add `async def get_all_users_summary(self) -> List[UserSummaryData]`:
    *   Fetch all `User` ORM objects, eager loading `roles`.
    *   Map each `User` ORM to `UserSummaryData` DTO.
2.  Add `async def get_user_by_id_for_edit(self, user_id: int) -> Optional[User]`:
    *   Fetch a single `User` by ID, eager loading `roles`. This ORM object will be used to populate an edit dialog later.
3.  Add `async def toggle_user_active_status(self, user_id_to_toggle: int, current_admin_user_id: int) -> Result[User]`:
    *   Prevent deactivating the current logged-in admin user or the last active admin.
    *   Fetch the user, toggle `is_active`, set `updated_at` and `updated_by` (if model has these directly, or rely on mixin).
    *   Save and return result.
4.  Add `async def get_all_roles(self) -> List[Role]`:
    *   Fetch all `Role` ORM objects. (Used later by `UserDialog` for role selection).
    *   **Checklist**: [ ] `get_all_users_summary` implemented. [ ] `get_user_by_id_for_edit` implemented. [ ] `toggle_user_active_status` implemented. [ ] `get_all_roles` implemented.

**III. UI Files**

1.  **Create `app/ui/settings/user_table_model.py`**:
    *   `UserTableModel(QAbstractTableModel)`.
    *   Headers: "Username", "Full Name", "Email", "Roles", "Active", "Last Login".
    *   `data()` method to correctly display fields from `UserSummaryData` (e.g., join role names list).
    *   Method to get `user_id` and `is_active` status for a given row.
    *   **Checklist**: [ ] Model class defined. [ ] Headers set. [ ] `rowCount`, `columnCount`, `headerData` implemented. [ ] `data` method implemented. [ ] Helper methods for ID/status implemented.

2.  **Create `app/ui/settings/user_management_widget.py`**:
    *   `UserManagementWidget(QWidget)`.
    *   `_init_ui()`:
        *   Toolbar with "Add User", "Edit User", "Toggle Active", "Change Password" (stubbed), "Refresh" actions.
        *   `QTableView` (`self.users_table`) using `UserTableModel`.
        *   Configure table view (selection, sorting, column sizing).
    *   `_load_users()` (async): Calls `SecurityManager.get_all_users_summary()` and updates table model via a slot.
    *   `_update_action_states()`: Enables/disables toolbar actions based on selection (e.g., can't toggle active for self).
    *   Action slots (`_on_add_user`, `_on_edit_user`, `_on_toggle_active`, `_on_change_password`): For now, they can show `QMessageBox.information("Not Implemented")` or simply log. `_on_toggle_active` will call the manager method.
    *   Initial data load.
    *   **Checklist**: [ ] Widget class defined. [ ] Toolbar and table view created. [ ] Actions stubbed. [ ] User list loads and displays. [ ] Action states update based on selection. [ ] Toggle active calls manager.

3.  **Update `app/ui/settings/settings_widget.py`**:
    *   Import `UserManagementWidget`.
    *   In `__init__` or a helper method, create an instance of `UserManagementWidget`.
    *   Add a new tab titled "Users" (or "User Management") to its `QTabWidget` and add the `UserManagementWidget` to it.
    *   **Checklist**: [ ] Import added. [ ] New tab added with `UserManagementWidget`.

4.  **Update `app/ui/settings/__init__.py`**:
    *   Export `UserManagementWidget` and `UserTableModel`.
    *   **Checklist**: [ ] Exports added.

I will now generate the required files.

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

# --- Company Setting DTO (existing, condensed) ---
class CompanySettingData(AppBaseModel, UserAuditData): 
    id: Optional[int] = None; company_name: str = Field(..., max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50); country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100); phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None; website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None; fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31); base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50); date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs (existing, condensed) ---
class FiscalYearCreateData(AppBaseModel, UserAuditData): 
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date; auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_fy_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        start, end = values.get('start_date'), values.get('end_date');
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): id: int; name: str; start_date: date; end_date: date; period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): id: int; year_name: str; start_date: date; end_date: date; is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = []

# --- Customer Related DTOs (existing, condensed) ---
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

# --- Vendor Related DTOs (existing, condensed) ---
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

# --- Product/Service Related DTOs (existing, condensed) ---
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

# --- Sales Invoice Related DTOs (existing, condensed) ---
class SalesInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None; description: str = Field(..., min_length=1, max_length=200); quantity: Decimal = Field(..., gt=Decimal(0)); unit_price: Decimal = Field(..., ge=Decimal(0)); discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100)); tax_code: Optional[str] = Field(None, max_length=20)
    dimension1_id: Optional[int] = None # Added from SalesInvoiceLine model
    dimension2_id: Optional[int] = None # Added from SalesInvoiceLine model
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

# --- NEW: User & Role Management DTOs ---
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
    roles: List[str] = [] # List of role names

class UserRoleAssignmentData(AppBaseModel): # For internal use when creating/updating user roles
    role_id: int

class UserBaseData(AppBaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    is_active: bool = True

class UserCreateInternalData(UserBaseData): # Used by SecurityManager internally
    password_hash: str # Manager will provide hash
    assigned_roles: List[UserRoleAssignmentData] = []

class UserCreateData(UserBaseData, UserAuditData): # For UI -> Manager
    password: str = Field(..., min_length=8)
    confirm_password: str
    assigned_role_ids: List[int] = []

    @root_validator(skip_on_failure=True)
    def passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('password'), values.get('confirm_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('Passwords do not match')
        return values

class UserUpdateData(UserBaseData, UserAuditData): # For UI -> Manager
    id: int
    assigned_role_ids: List[int] = []
    # Password changes are handled by a separate DTO/endpoint for security
    # Username change might be disallowed or handled with care due to uniqueness

class UserPasswordChangeData(AppBaseModel, UserAuditData):
    user_id_to_change: int # ID of user whose password is to be changed
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    # Optionally, if admin changes for other user, or user changes own:
    # old_password: Optional[str] = None # Required if user changes their own password

    @root_validator(skip_on_failure=True)
    def new_passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('new_password'), values.get('confirm_new_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('New passwords do not match')
        return values

```

---
**2. Update `app/core/security_manager.py`**
```python
# File: app/core/security_manager.py
import bcrypt
from typing import Optional, List, cast
from app.models.core.user import User, Role, Permission # Added Permission
from app.models.accounting.account import Account # For type hint in other parts of app, not directly used here
from sqlalchemy import select, update, delete # Added delete
from sqlalchemy.orm import selectinload, joinedload
from app.core.database_manager import DatabaseManager 
import datetime 
from app.utils.result import Result
from app.utils.pydantic_models import (
    UserSummaryData, UserCreateInternalData, UserRoleAssignmentData,
    UserUpdateData, UserPasswordChangeData # New DTOs
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
                    await session.commit() # Commit last_login and failed_attempts reset
                    return user
                else: 
                    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                    user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
                    if user.failed_login_attempts >= 5: # Lock account after 5 attempts
                        user.is_active = False 
                        # Log account lockout event
                        if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                             self.db_manager.logger.warning(f"User account '{username}' locked due to too many failed login attempts.")
                    await session.commit() # Commit failed attempt info
            elif user and not user.is_active:
                if hasattr(self.db_manager, 'logger') and self.db_manager.logger:
                    self.db_manager.logger.warning(f"Login attempt for inactive user account '{username}'.")
                user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc) # Still record attempt
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
        # Assuming 'Administrator' role has all permissions implicitly in many systems
        # Or check for specific superuser flag on user if exists
        if any(role.name == 'Administrator' for role in self.current_user.roles):
            return True # Administrators have all permissions
        if not self.current_user.roles:
             return False 
        for role in self.current_user.roles:
            if not role.permissions: continue
            for perm in role.permissions:
                if perm.code == required_permission_code:
                    return True
        return False

    async def create_user_from_internal_data(self, user_data: UserCreateInternalData) -> Result[User]:
        """Creates a user from UserCreateInternalData (expects password_hash)."""
        async with self.db_manager.session() as session:
            stmt_exist = select(User).where(User.username == user_data.username)
            if (await session.execute(stmt_exist)).scalars().first():
                return Result.failure([f"Username '{user_data.username}' already exists."])
            if user_data.email:
                stmt_email_exist = select(User).where(User.email == user_data.email)
                if (await session.execute(stmt_email_exist)).scalars().first():
                    return Result.failure([f"Email '{user_data.email}' already registered."])

            new_user = User(
                username=user_data.username, password_hash=user_data.password_hash, 
                email=str(user_data.email) if user_data.email else None, # Ensure EmailStr is converted
                full_name=user_data.full_name, is_active=user_data.is_active,
            )
            
            if user_data.assigned_roles:
                role_ids = [r.role_id for r in user_data.assigned_roles]
                roles_q = await session.execute(select(Role).where(Role.id.in_(role_ids))) # type: ignore
                db_roles = roles_q.scalars().all()
                if len(db_roles) != len(role_ids):
                    # Log or handle missing roles if necessary
                    pass 
                new_user.roles.extend(db_roles) 
            
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            return Result.success(new_user)
            
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
                    email=user.email, # Pydantic will handle EmailStr conversion if needed
                    is_active=user.is_active,
                    last_login=user.last_login,
                    roles=[role.name for role in user.roles]
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

            # Check for username collision if username is being changed
            if dto.username != user_to_update.username:
                stmt_exist = select(User).where(User.username == dto.username, User.id != dto.id)
                if (await session.execute(stmt_exist)).scalars().first():
                    return Result.failure([f"Username '{dto.username}' already exists for another user."])
            
            if dto.email and dto.email != user_to_update.email:
                stmt_email_exist = select(User).where(User.email == dto.email, User.id != dto.id)
                if (await session.execute(stmt_email_exist)).scalars().first():
                    return Result.failure([f"Email '{dto.email}' already registered by another user."])

            user_to_update.username = dto.username
            user_to_update.full_name = dto.full_name
            user_to_update.email = str(dto.email) if dto.email else None
            user_to_update.is_active = dto.is_active
            # user_to_update.updated_by_user_id = dto.user_id # Model doesn't have this yet, UserAuditMixin is not used

            # Role management
            if dto.assigned_role_ids is not None: # Check if it's provided, even if empty list
                # Fetch new roles
                new_roles_orm: List[Role] = []
                if dto.assigned_role_ids:
                    roles_q = await session.execute(select(Role).where(Role.id.in_(dto.assigned_role_ids))) # type: ignore
                    new_roles_orm = list(roles_q.scalars().all())
                
                # Efficiently update roles: clear existing and add new ones
                user_to_update.roles.clear() # Clear the existing collection
                for role_orm in new_roles_orm: # Add new roles
                    user_to_update.roles.append(role_orm)

            await session.flush()
            await session.refresh(user_to_update)
            if user_to_update.roles: # Ensure roles are loaded after update
                await session.refresh(user_to_update, attribute_names=['roles'])
            return Result.success(user_to_update)


    async def toggle_user_active_status(self, user_id_to_toggle: int, current_admin_user_id: int) -> Result[User]:
        if user_id_to_toggle == current_admin_user_id:
            return Result.failure(["Cannot deactivate your own account."])

        async with self.db_manager.session() as session:
            user = await session.get(User, user_id_to_toggle)
            if not user:
                return Result.failure([f"User with ID {user_id_to_toggle} not found."])

            # Prevent deactivating the last active admin user
            if not user.is_active: # If trying to activate, it's fine
                pass
            else: # If trying to deactivate
                admin_role = (await session.execute(select(Role).where(Role.name == "Administrator"))).scalars().first()
                if admin_role and admin_role in user.roles: # type: ignore
                    # Check if this is the last active admin
                    active_admins_count_stmt = select(func.count(User.id)).join(User.roles).where( # type: ignore
                        Role.name == "Administrator", User.is_active == True
                    )
                    active_admins_count = (await session.execute(active_admins_count_stmt)).scalar_one()
                    if active_admins_count <= 1:
                        return Result.failure(["Cannot deactivate the last active administrator."])
            
            user.is_active = not user.is_active
            # user.updated_by = current_admin_user_id # If User model has this
            user.updated_at = datetime.datetime.now(datetime.timezone.utc) # Manually update if mixin isn't on User
            
            await session.flush()
            await session.refresh(user)
            return Result.success(user)

    async def get_all_roles(self) -> List[Role]:
        async with self.db_manager.session() as session:
            stmt = select(Role).order_by(Role.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def change_user_password(self, user_id_to_change: int, new_password_dto: UserPasswordChangeData) -> Result[None]:
        # Assuming current_admin_user_id is from new_password_dto.user_id (the one performing action)
        # For now, only admin can change other user's password or user their own (if old_password matched)
        # This simplified version assumes admin is changing password for another user, or user for themselves with validation.
        
        if new_password_dto.user_id_to_change == new_password_dto.user_id:
            # User changing their own password - would need old_password verification
            # For this iteration, let's simplify: an admin (current_user) changes password for user_id_to_change
            pass # This part is not fully fleshed out for self-change vs admin-change yet
        
        # Password confirmation happens in DTO.

        async with self.db_manager.session() as session:
            user = await session.get(User, user_id_to_change)
            if not user:
                return Result.failure([f"User with ID {user_id_to_change} not found."])
            
            user.password_hash = self.hash_password(new_password_dto.new_password)
            user.require_password_change = False # If admin changes, or user successfully changes.
            user.updated_at = datetime.datetime.now(datetime.timezone.utc)
            
            await session.flush()
            return Result.success(None)

```

---
**3. Create `app/ui/settings/user_table_model.py`**
```python
# app/ui/settings/user_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.utils.pydantic_models import UserSummaryData

class UserTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[UserSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Username", "Full Name", "Email", "Roles", "Active", "Last Login"]
        self._data: List[UserSummaryData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        user_summary: UserSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace(' ', '_')
            
            if col == 0: return str(user_summary.id)
            if col == 1: return user_summary.username
            if col == 2: return user_summary.full_name or ""
            if col == 3: return str(user_summary.email) if user_summary.email else ""
            if col == 4: return ", ".join(user_summary.roles) if user_summary.roles else "N/A"
            if col == 5: return "Yes" if user_summary.is_active else "No"
            if col == 6: 
                return user_summary.last_login.strftime('%d/%m/%Y %H:%M') if user_summary.last_login else "Never"
            
            return str(getattr(user_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: # Store ID with the first column
                return user_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_user_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None: return int(id_val)
            return self._data[row].id 
        return None
        
    def get_user_active_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[UserSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

---
**4. Create `app/ui/settings/user_management_widget.py`**
```python
# app/ui/settings/user_management_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.settings.user_table_model import UserTableModel
# from app.ui.settings.user_dialog import UserDialog # To be created in Part 2
from app.utils.pydantic_models import UserSummaryData
from app.utils.json_helpers import json_converter, json_date_hook # json_date_hook might be needed for last_login
from app.utils.result import Result
from app.models.core.user import User # For Result type hint

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class UserManagementWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass # Use default path
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_users()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        # Filter area can be added later if needed

        self.users_table = QTableView()
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.users_table.horizontalHeader().setStretchLastSection(True) 
        self.users_table.setSortingEnabled(True)

        self.table_model = UserTableModel()
        self.users_table.setModel(self.table_model)
        
        header = self.users_table.horizontalHeader()
        # Set default resize mode for all columns first
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Hide ID column
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.users_table.setColumnHidden(id_col_idx, True)
        
        # Stretch "Full Name" or "Email" column if "Full Name" isn't prominent
        fn_col_idx = self.table_model._headers.index("Full Name") if "Full Name" in self.table_model._headers else -1
        if fn_col_idx != -1 and not self.users_table.isColumnHidden(fn_col_idx) :
            header.setSectionResizeMode(fn_col_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model._headers.index("Email") if "Email" in self.table_model._headers else -1 != -1:
            email_col_idx = self.table_model._headers.index("Email")
            if not self.users_table.isColumnHidden(email_col_idx):
                 header.setSectionResizeMode(email_col_idx, QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.users_table)
        self.setLayout(self.main_layout)

        if self.users_table.selectionModel():
            self.users_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("User Management Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add User", self)
        self.toolbar_add_action.triggered.connect(self._on_add_user)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit User", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_user)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar_change_password_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Change Password", self) # Reusing icon
        self.toolbar_change_password_action.triggered.connect(self._on_change_password)
        self.toolbar.addAction(self.toolbar_change_password_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_users()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _update_action_states(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_modify = False
        is_current_user_selected = False

        if single_selection:
            can_modify = True
            row = selected_rows[0].row()
            user_id = self.table_model.get_user_id_at_row(row)
            if self.app_core.current_user and user_id == self.app_core.current_user.id:
                is_current_user_selected = True
        
        self.toolbar_edit_action.setEnabled(can_modify)
        self.toolbar_toggle_active_action.setEnabled(can_modify and not is_current_user_selected) # Can't toggle self
        self.toolbar_change_password_action.setEnabled(can_modify) # Admin can change anyone, user can change self

    async def _load_users(self):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Security Manager component not available."))
            return
        try:
            summaries: List[UserSummaryData] = await self.app_core.security_manager.get_all_users_summary()
            json_data = json.dumps([s.model_dump() for s in summaries], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading users: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            user_summaries: List[UserSummaryData] = [UserSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(user_summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate user data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_user(self):
        QMessageBox.information(self, "Add User", "User creation dialog not yet implemented.\nPlease use initial_data.sql or direct DB operations for now.")
        # Placeholder for when UserDialog is ready:
        # if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        # dialog = UserDialog(self.app_core, self.app_core.current_user.id, parent=self)
        # dialog.user_saved.connect(lambda: schedule_task_from_qt(self._load_users()))
        # dialog.exec()

    def _get_selected_user_id(self) -> Optional[int]:
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None
        return self.table_model.get_user_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_user(self):
        user_id = self._get_selected_user_id()
        if user_id is None: QMessageBox.information(self, "Selection", "Please select a single user to edit."); return
        QMessageBox.information(self, "Edit User", f"User editing dialog for ID {user_id} not yet implemented.")
        # Placeholder for when UserDialog is ready:
        # if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        # dialog = UserDialog(self.app_core, self.app_core.current_user.id, user_id_to_edit=user_id, parent=self)
        # dialog.user_saved.connect(lambda: schedule_task_from_qt(self._load_users()))
        # dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        user_id = self._get_selected_user_id()
        if user_id is None: QMessageBox.information(self, "Selection", "Please select a single user to toggle status."); return
        
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        if user_id == self.app_core.current_user.id:
            QMessageBox.warning(self, "Action Denied", "You cannot change the active status of your own account.")
            return
            
        current_row_idx = self.users_table.currentIndex().row()
        is_currently_active = self.table_model.get_user_active_status_at_row(current_row_idx)
        action_verb = "deactivate" if is_currently_active else "activate"
        
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this user account?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.security_manager.toggle_user_active_status(user_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule user status toggle."); return
        try:
            result: Result[User] = future.result()
            if result.is_success and result.value:
                action_verb_past = "activated" if result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"User account {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_users()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle user status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for user: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    @Slot()
    def _on_change_password(self):
        user_id = self._get_selected_user_id()
        if user_id is None: QMessageBox.information(self, "Selection", "Please select a user to change password."); return
        QMessageBox.information(self, "Change Password", f"Password change dialog for user ID {user_id} not yet implemented.")
        # Placeholder for when ChangePasswordDialog is ready

```

---
**5. Update `app/ui/settings/settings_widget.py`**
```python
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView,
                               QHBoxLayout, QTabWidget # Added QTabWidget
                               ) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt, QAbstractTableModel, QModelIndex 
from PySide6.QtGui import QColor
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData, FiscalYearCreateData, FiscalYearData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from app.models.accounting.fiscal_year import FiscalYear 
from app.ui.accounting.fiscal_year_dialog import FiscalYearDialog 
from app.ui.settings.user_management_widget import UserManagementWidget # New Import
from decimal import Decimal, InvalidOperation
import asyncio
import json 
from typing import Optional, List, Any, Dict 
from app.main import schedule_task_from_qt 
from datetime import date as python_date, datetime 
from app.utils.json_helpers import json_converter, json_date_hook 

class FiscalYearTableModel(QAbstractTableModel):
    def __init__(self, data: List[FiscalYearData] = None, parent=None): # type: ignore
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
            return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        
        try:
            fy = self._data[index.row()]
            column = index.column()

            if column == 0: return fy.year_name
            if column == 1: return fy.start_date.strftime('%d/%m/%Y') if isinstance(fy.start_date, python_date) else str(fy.start_date)
            if column == 2: return fy.end_date.strftime('%d/%m/%Y') if isinstance(fy.end_date, python_date) else str(fy.end_date)
            if column == 3: return "Closed" if fy.is_closed else "Open"
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
        
        self.main_layout = QVBoxLayout(self) # Changed from self.layout
        self.tab_widget = QTabWidget() # Create TabWidget
        self.main_layout.addWidget(self.tab_widget)

        # --- Company Settings Tab ---
        self.company_settings_tab = QWidget()
        company_tab_layout = QVBoxLayout(self.company_settings_tab) # Layout for this tab

        company_settings_group = QGroupBox("Company Information")
        company_settings_form_layout = QFormLayout(company_settings_group) # Use specific form layout

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
        self.tab_widget.addTab(self.company_settings_tab, "Company")


        # --- Fiscal Year Management Tab ---
        self.fiscal_year_tab = QWidget()
        fiscal_tab_main_layout = QVBoxLayout(self.fiscal_year_tab)
        
        fiscal_year_group = QGroupBox("Fiscal Year Management")
        fiscal_year_group_layout = QVBoxLayout(fiscal_year_group) # Layout for this groupbox

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
        fiscal_tab_main_layout.addStretch() # Add stretch to push group to top
        self.tab_widget.addTab(self.fiscal_year_tab, "Fiscal Years")

        # --- User Management Tab (NEW) ---
        self.user_management_widget = UserManagementWidget(self.app_core)
        self.tab_widget.addTab(self.user_management_widget, "Users")
        
        self.setLayout(self.main_layout) # Set main_layout for SettingsWidget

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
                self.app_core.logger.error(error_msg, exc_info=True) # Log with traceback
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
        except json.JSONDecodeError: currencies_data = [{"code": "SGD", "name": "Singapore Dollar"}] # Fallback
            
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
                idx_sgd = self.base_currency_combo.findData("SGD") # Default to SGD if current not found
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
            id=1, company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None, uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None, gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            address_line1=self.address_line1_edit.text() or None, address_line2=self.address_line2_edit.text() or None,
            postal_code=self.postal_code_edit.text() or None, city=self.city_edit.text() or "Singapore",
            country=self.country_edit.text() or "Singapore", contact_person=self.contact_person_edit.text() or None,
            phone=self.phone_edit.text() or None, email=self.email_edit.text() or None, # Will be validated by Pydantic if EmailStr
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
            # Use model_dump for Pydantic v2
            update_dict = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            for field_name, field_value in update_dict.items():
                if hasattr(orm_obj_to_save, field_name): 
                    if field_name == 'email' and field_value is not None: # Pydantic EmailStr might be object
                        setattr(orm_obj_to_save, field_name, str(field_value))
                    else:
                        setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            # Ensure email is string if Pydantic EmailStr object
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
            fy_dict_list = json.loads(fy_json_list_str, object_hook=json_date_hook) # Use hook
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
**6. Update `app/ui/settings/__init__.py`**
```python
# File: app/ui/settings/__init__.py
from .settings_widget import SettingsWidget
from .user_management_widget import UserManagementWidget # New Import
from .user_table_model import UserTableModel # New Import

__all__ = [
    "SettingsWidget",
    "UserManagementWidget", # New Export
    "UserTableModel",       # New Export
]

```
