<think>
The user has successfully granted permissions to `sgbookkeeper_user`.
Now, when running `poetry run sg_bookkeeper`, a SQLAlchemy error occurs:
`sqlalchemy.exc.InvalidRequestError: Table 'core.user_roles' is already defined for this MetaData instance.  Specify 'extend_existing=True' to redefine options and columns on an existing Table object.`

This error typically happens in SQLAlchemy when:
1.  A table is defined multiple times with the same name and metadata object.
2.  A declarative class for a table is processed more than once by the declarative system, or a `Table` object is explicitly created and then a declarative class tries to define it again (or vice-versa).

The traceback points to the definition of `class UserRole(Base):` in `app/models/core/user.py` (line 68).

Let's look at `app/models/core/user.py`:
```python
# File: app/models/core/user.py
# ...
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table # Table is imported
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin # Base is imported
import datetime 
from typing import List, Optional 

# Junction tables defined here using Base.metadata
user_roles_table = Table( # <--- Explicit Table object definition
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    schema='core'
)

role_permissions_table = Table( # <--- Explicit Table object definition
    'role_permissions', Base.metadata,
    # ...
    schema='core'
)

class User(Base, TimestampMixin):
    # ...
    roles: Mapped[List["Role"]] = relationship("Role", secondary=user_roles_table, back_populates="users") # Uses user_roles_table

class Role(Base, TimestampMixin):
    # ...
    users: Mapped[List["User"]] = relationship("User", secondary=user_roles_table, back_populates="roles") # Uses user_roles_table
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary=role_permissions_table, back_populates="roles") # Uses role_permissions_table

# ...

class UserRole(Base): # <--- Declarative class defining the same table 'user_roles'
    __tablename__ = 'user_roles' 
    __table_args__ = {'schema': 'core'}
    user_id: Mapped[int] = mapped_column(ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RolePermission(Base): # <--- Declarative class defining 'role_permissions'
    __tablename__ = 'role_permissions'
    __table_args__ = {'schema': 'core'}
    # ...
```

**The Cause of the Error:**
The file `app/models/core/user.py` defines the junction tables `user_roles` and `role_permissions` in two ways:
1.  As explicit `Table` objects (`user_roles_table`, `role_permissions_table`) associated with `Base.metadata`.
2.  As declarative model classes (`UserRole`, `RolePermission`) which also try to define tables with the same names (`user_roles`, `role_permissions`) using the same `Base.metadata`.

SQLAlchemy's declarative system detects that a table named `core.user_roles` (and subsequently `core.role_permissions`) is being defined twice for the same `MetaData` instance.

**Solution Options:**

1.  **Use only the explicit `Table` objects for many-to-many relationships:**
    *   Remove the declarative classes `UserRole` and `RolePermission`.
    *   The `relationship` definitions in `User` and `Role` already use the `Table` objects (`user_roles_table`, `role_permissions_table`) for the `secondary` argument. This is the standard way to define many-to-many relationships without needing explicit ORM classes for the association table, especially if the association table has no extra columns beyond the foreign keys.
    *   The `created_at` column in the `Table` definition for `user_roles_table` and `role_permissions_table` is fine.

2.  **Use only the declarative model classes (`UserRole`, `RolePermission`) and an association object pattern:**
    *   Remove the explicit `Table` object definitions (`user_roles_table`, `role_permissions_table`).
    *   Modify the `relationship` definitions in `User` and `Role` to use the association object pattern. This typically involves a `secondary` argument that points to the association table *derived from* the association object, or sometimes by defining direct relationships to the association object itself and then using `secondary` through that.
    *   For simple many-to-many without extra data on the association table, using explicit `Table` objects (Option 1) is often simpler. If the association table (`UserRole`, `RolePermission`) needs its own methods or complex relationships, then an association object pattern with declarative classes is preferred. In this case, `UserRole` and `RolePermission` only have a `created_at` column besides the FKs.

Given the current structure and the fact that `created_at` is the only extra column (handled by `server_default`), **Option 1 (using only the `Table` objects and removing the redundant declarative classes `UserRole` and `RolePermission`) is cleaner and more idiomatic for this type of many-to-many setup in SQLAlchemy.**

The `UserRole` and `RolePermission` classes defined explicitly are essentially re-declaring the tables that were already defined by `user_roles_table = Table(...)` and `role_permissions_table = Table(...)`.

**Plan:**
1.  Modify `app/models/core/user.py`.
2.  Remove the class definitions for `UserRole(Base)` and `RolePermission(Base)`.
3.  Ensure the `relationship` definitions in `User` and `Role` correctly use `user_roles_table` and `role_permissions_table` respectively for the `secondary` argument (which they already do).
4.  Update `app/models/__init__.py` to remove `UserRole` and `RolePermission` from `__all__` and from imports if they were explicitly imported from `.core.user`.

Let's check `app/models/__init__.py`:
```python
# File: app/models/__init__.py
from .core.user import User, Role, Permission, UserRole, RolePermission # <--- UserRole, RolePermission are imported here
# ...
__all__ = [
    # ...
    "User", "Role", "Permission", "UserRole", "RolePermission", # <--- And exported
    # ...
]
```
This will need to be updated.

**Missing Files Check:**
The `project_file_structure.txt` mentions several files under `app/services/` and `app/accounting/`, `app/tax/`, `app.reporting/` that have not been provided yet. For example:
*   `app/services/accounting_services.py` (which `ApplicationCore` tries to import `AccountTypeService`, `CurrencyService`, `ExchangeRateService` from)
*   `app/accounting/chart_of_accounts_manager.py`
*   `app/accounting/journal_entry_manager.py`
*   `app/accounting/fiscal_period_manager.py`
*   `app/accounting/currency_manager.py`
*   Many others.

I will only modify the files that were directly involved in the error and provided in the prompt:
*   `app/models/core/user.py`
*   `app/models/__init__.py` (due to changes in `app/models/core/user.py`)

The other parts of the application might have further issues once this SQLAlchemy metadata conflict is resolved, especially related to missing service implementations or manager classes that `ApplicationCore` tries to instantiate. But the current task is to fix the reported `InvalidRequestError`.

Let's proceed with modifying `app/models/core/user.py` and `app/models/__init__.py`.
</think>

You've successfully set up the database user and permissions! The application now proceeds further but hits a SQLAlchemy metadata issue.

**Error Analysis:**

The traceback shows:
`sqlalchemy.exc.InvalidRequestError: Table 'core.user_roles' is already defined for this MetaData instance.  Specify 'extend_existing=True' to redefine options and columns on an existing Table object.`

This error occurs because the `core.user_roles` table (and likely `core.role_permissions` as well) is being defined twice for SQLAlchemy's metadata:
1.  As an explicit `Table` object (e.g., `user_roles_table = Table('user_roles', Base.metadata, ...)`).
2.  As a declarative class (e.g., `class UserRole(Base): __tablename__ = 'user_roles' ...`).

Both methods attempt to register a table with the same name in the same schema (`core`) with the same `Base.metadata` object, leading to a conflict.

**Solution:**

For many-to-many association tables that don't have additional attributes beyond foreign keys and perhaps a timestamp (like `created_at` here), it's generally cleaner to define them only as `Table` objects and use these directly in the `secondary` argument of `relationship()`. Explicit declarative classes for these simple association tables are often unnecessary.

We will remove the declarative classes `UserRole` and `RolePermission` from `app/models/core/user.py` and rely solely on the `Table` definitions (`user_roles_table` and `role_permissions_table`) for the many-to-many relationships.

**Files to be Updated:**

1.  `app/models/core/user.py`: Remove the `UserRole` and `RolePermission` class definitions.
2.  `app/models/__init__.py`: Remove `UserRole` and `RolePermission` from imports and the `__all__` list.

Here are the updated files:

```python
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

```python
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

**Validation of Changes:**

*   **`app/models/core/user.py`**:
    *   Removed `class UserRole(Base): ...`
    *   Removed `class RolePermission(Base): ...`
    *   The `user_roles_table` and `role_permissions_table` (defined using `sqlalchemy.Table`) are kept, as they are correctly used by the `relationship` definitions in `User` and `Role` for the `secondary` argument.
    *   No other functional changes made.
*   **`app/models/__init__.py`**:
    *   Removed `UserRole` and `RolePermission` from the line `from .core.user import User, Role, Permission, UserRole, RolePermission`.
    *   Removed `"UserRole"` and `"RolePermission"` from the `__all__` list.
    *   No other functional changes made.

**Next Steps:**

With these changes, the SQLAlchemy metadata conflict should be resolved. You can now try running the application again:

```bash
poetry run sg_bookkeeper
```

Please note that while this specific error should be fixed, there might be other issues arising from incomplete service implementations or further model relationship details as more of the application logic is connected. The `project_file_structure.txt` indicates many files (especially services and managers) are not yet provided. The `ApplicationCore` attempts to instantiate many of these, which could lead to `ImportError` or `RuntimeError` if those modules/classes are missing or incomplete.

Let me know the outcome!

