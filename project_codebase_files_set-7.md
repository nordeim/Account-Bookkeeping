# app/models/accounting/__init__.py
```py
# File: app/models/accounting/__init__.py
# New __init__.py for accounting models if moved to subdirectories
from .account_type import AccountType
from .currency import Currency
from .exchange_rate import ExchangeRate
from .account import Account
from .fiscal_year import FiscalYear
from .fiscal_period import FiscalPeriod
from .journal_entry import JournalEntry, JournalEntryLine
from .recurring_pattern import RecurringPattern
from .dimension import Dimension
from .budget import Budget, BudgetDetail
from .tax_code import TaxCode
from .gst_return import GSTReturn
from .withholding_tax_certificate import WithholdingTaxCertificate

__all__ = [
    "AccountType", "Currency", "ExchangeRate", "Account",
    "FiscalYear", "FiscalPeriod", "JournalEntry", "JournalEntryLine",
    "RecurringPattern", "Dimension", "Budget", "BudgetDetail",
    "TaxCode", "GSTReturn", "WithholdingTaxCertificate",
]

```

# app/models/accounting/withholding_tax_certificate.py
```py
# File: app/models/accounting/withholding_tax_certificate.py
# (Content previously generated, but now placed in this path)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.business.vendor import Vendor 
import datetime
from decimal import Decimal
from typing import Optional

class WithholdingTaxCertificate(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'withholding_tax_certificates'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Issued', 'Voided')", name='ck_wht_certs_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    certificate_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.vendors.id'), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(50), nullable=False) 
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False)
    payment_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount_before_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Draft', nullable=False)
    issue_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

    vendor: Mapped["Vendor"] = relationship() 

```

# app/models/accounting/account.py
```py
# File: app/models/accounting/account.py
# (Moved from app/models/account.py and fields updated - completing relationships)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, CheckConstraint, Date, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import List, Optional 
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin 
from app.models.core.user import User 

# Forward string declarations for relationships
# These will be resolved by SQLAlchemy based on the string hints.
# "JournalEntryLine", "BudgetDetail", "TaxCode", "Customer", "Vendor", 
# "Product", "BankAccount"

class Account(Base, TimestampMixin):
    __tablename__ = 'accounts'
    __table_args__ = (
         CheckConstraint("account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_accounts_account_type_category'),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    sub_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tax_treatment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) 
    gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    
    report_group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_control_account: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bank_account: Mapped[bool] = mapped_column(Boolean, default=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    opening_balance_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
        
    # Self-referential relationship for parent/children
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
    
    # Relationships to User for audit trails
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

    # Relationships defined by other models via back_populates
    journal_lines: Mapped[List["JournalEntryLine"]] = relationship(back_populates="account") # type: ignore
    budget_details: Mapped[List["BudgetDetail"]] = relationship(back_populates="account") # type: ignore
    
    # For TaxCode.affects_account_id
    tax_code_applications: Mapped[List["TaxCode"]] = relationship(back_populates="affects_account") # type: ignore
    
    # For Customer.receivables_account_id
    customer_receivables_links: Mapped[List["Customer"]] = relationship(back_populates="receivables_account") # type: ignore
    
    # For Vendor.payables_account_id
    vendor_payables_links: Mapped[List["Vendor"]] = relationship(back_populates="payables_account") # type: ignore
    
    # For Product fields (sales_account_id, purchase_account_id, inventory_account_id)
    product_sales_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.sales_account_id", back_populates="sales_account") # type: ignore
    product_purchase_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.purchase_account_id", back_populates="purchase_account") # type: ignore
    product_inventory_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.inventory_account_id", back_populates="inventory_account") # type: ignore

    # For BankAccount.gl_account_id
    bank_account_links: Mapped[List["BankAccount"]] = relationship(back_populates="gl_account") # type: ignore


    def to_dict(self): # Kept from previous version, might be useful
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'account_type': self.account_type,
            'sub_type': self.sub_type,
            'parent_id': self.parent_id,
            'is_active': self.is_active,
            'description': self.description,
            'report_group': self.report_group,
            'is_control_account': self.is_control_account,
            'is_bank_account': self.is_bank_account,
            'opening_balance': self.opening_balance,
            'opening_balance_date': self.opening_balance_date,
        }

```

# app/models/accounting/gst_return.py
```py
# File: app/models/accounting/gst_return.py
# (Moved from app/models/gst_return.py and updated)
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry

class GSTReturn(Base, TimestampMixin):
    __tablename__ = 'gst_returns'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Submitted', 'Amended')", name='ck_gst_returns_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    return_period: Mapped[str] = mapped_column(String(20), unique=True, nullable=False) 
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    filing_due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    standard_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    zero_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    exempt_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    total_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    taxable_purchases: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    output_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    input_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    tax_adjustments: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    tax_payable: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    status: Mapped[str] = mapped_column(String(20), default='Draft')
    submission_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    submission_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # No back_populates needed for one-to-one/opt-one
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/accounting/budget.py
```py
# File: app/models/accounting/budget.py
# (Moved from app/models/budget.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.fiscal_period import FiscalPeriod 
from app.models.accounting.dimension import Dimension 
from app.models.core.user import User
from typing import List, Optional 
from decimal import Decimal 

class Budget(Base, TimestampMixin): 
    __tablename__ = 'budgets'
    __table_args__ = {'schema': 'accounting'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False) 
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    fiscal_year_obj: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="budgets")
    details: Mapped[List["BudgetDetail"]] = relationship("BudgetDetail", back_populates="budget", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class BudgetDetail(Base, TimestampMixin): 
    __tablename__ = 'budget_details'
    __table_args__ = (
        # Reference schema has COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0) in UNIQUE.
        # This means NULLs are treated as 0 for uniqueness.
        # This is harder to model directly in SQLAlchemy UniqueConstraint if DB doesn't support function-based indexes for it directly.
        # For PostgreSQL, function-based unique indexes are possible.
        # For now, simple UniqueConstraint. DB schema will have the COALESCE logic.
        UniqueConstraint('budget_id', 'account_id', 'fiscal_period_id', 'dimension1_id', 'dimension2_id', name='uq_budget_details_key_dims_nullable'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    budget_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.budgets.id', ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    budget: Mapped["Budget"] = relationship("Budget", back_populates="details")
    account: Mapped["Account"] = relationship("Account", back_populates="budget_details")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod", back_populates="budget_details")
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

# Add back-populates to Account and FiscalPeriod
Account.budget_details = relationship("BudgetDetail", back_populates="account") # type: ignore
FiscalPeriod.budget_details = relationship("BudgetDetail", back_populates="fiscal_period") # type: ignore

```

# app/models/accounting/exchange_rate.py
```py
# File: app/models/accounting/exchange_rate.py
# (Moved from app/models/exchange_rate.py and fields updated)
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.currency import Currency 
from app.models.core.user import User 
import datetime 
from decimal import Decimal 
from typing import Optional

class ExchangeRate(Base, TimestampMixin):
    __tablename__ = 'exchange_rates'
    __table_args__ = (
        UniqueConstraint('from_currency', 'to_currency', 'rate_date', name='uq_exchange_rates_pair_date'), 
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    from_currency_code: Mapped[str] = mapped_column("from_currency", String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    to_currency_code: Mapped[str] = mapped_column("to_currency", String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    rate_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    exchange_rate_value: Mapped[Decimal] = mapped_column("exchange_rate", Numeric(15, 6), nullable=False) # Renamed attribute
    
    created_by_user_id: Mapped[Optional[int]] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=True)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True)

    from_currency_obj: Mapped["Currency"] = relationship("Currency", foreign_keys=[from_currency_code]) 
    to_currency_obj: Mapped["Currency"] = relationship("Currency", foreign_keys=[to_currency_code]) 
    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/accounting/journal_entry.py
```py
# File: app/models/accounting/journal_entry.py
# (Moved from app/models/journal_entry.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func
from typing import List, Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.core.user import User
from app.models.accounting.currency import Currency
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension
# from app.models.accounting.recurring_pattern import RecurringPattern # Forward reference with string

class JournalEntry(Base, TimestampMixin):
    __tablename__ = 'journal_entries'
    __table_args__ = {'schema': 'accounting'}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    entry_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    journal_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    entry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_pattern_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.recurring_patterns.id'), nullable=True)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversing_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', use_alter=True, name='fk_je_reversing_entry_id'), nullable=True)
    
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod", back_populates="journal_entries")
    lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")
    generated_from_pattern: Mapped[Optional["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys=[recurring_pattern_id], back_populates="generated_journal_entries") # type: ignore
    
    reversing_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversing_entry_id], uselist=False, post_update=True) # type: ignore
    template_for_patterns: Mapped[List["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys="RecurringPattern.template_entry_id", back_populates="template_journal_entry") # type: ignore


    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class JournalEntryLine(Base, TimestampMixin): 
    __tablename__ = 'journal_entry_lines'
    __table_args__ = (
        CheckConstraint(
            " (debit_amount > 0 AND credit_amount = 0) OR "
            " (credit_amount > 0 AND debit_amount = 0) OR "
            " (debit_amount = 0 AND credit_amount = 0) ", 
            name='jel_check_debit_credit'
        ),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    journal_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD')
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15, 6), default=Decimal(1))
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
        
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account", back_populates="journal_lines")
    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code])
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code])
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])
    
    @validates('debit_amount', 'credit_amount')
    def validate_amounts(self, key, value):
        value_decimal = Decimal(str(value)) 
        if key == 'debit_amount' and value_decimal > Decimal(0):
            self.credit_amount = Decimal(0)
        elif key == 'credit_amount' and value_decimal > Decimal(0):
            self.debit_amount = Decimal(0)
        return value_decimal

# Update Account relationships for journal_lines
Account.journal_lines = relationship("JournalEntryLine", back_populates="account") # type: ignore

```

# app/models/accounting/fiscal_year.py
```py
# File: app/models/accounting/fiscal_year.py
# (Previously generated as app/models/fiscal_year.py, reviewed and confirmed)
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import DATERANGE # For GIST constraint if modeled in SQLAlchemy
# from sqlalchemy.sql.functions import GenericFunction # For functions like `daterange`
# from sqlalchemy.sql import literal_column
from app.models.base import Base, TimestampMixin # UserAuditMixin handled directly
from app.models.core.user import User
import datetime
from typing import List, Optional

class FiscalYear(Base, TimestampMixin):
    __tablename__ = 'fiscal_years'
    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='fy_date_range_check'),
        # The EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
        # is a database-level constraint. SQLAlchemy doesn't model EXCLUDE directly in Core/ORM easily.
        # It's enforced by the DB schema from schema.sql.
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[Optional[int]] = mapped_column("closed_by", Integer, ForeignKey('core.users.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by",Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by",Integer, ForeignKey('core.users.id'), nullable=False)

    # Relationships
    closed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[closed_by_user_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    fiscal_periods: Mapped[List["FiscalPeriod"]] = relationship("FiscalPeriod", back_populates="fiscal_year") # type: ignore
    budgets: Mapped[List["Budget"]] = relationship("Budget", back_populates="fiscal_year_obj") # type: ignore

```

# app/models/accounting/fiscal_period.py
```py
# File: app/models/accounting/fiscal_period.py
# (Moved from app/models/fiscal_period.py and updated)
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, UniqueConstraint, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.core.user import User
from typing import Optional, List

class FiscalPeriod(Base, TimestampMixin):
    __tablename__ = 'fiscal_periods'
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'period_type', 'period_number', name='fp_unique_period_dates'),
        CheckConstraint('start_date <= end_date', name='fp_date_range_check'),
        CheckConstraint("period_type IN ('Month', 'Quarter', 'Year')", name='ck_fp_period_type'),
        CheckConstraint("status IN ('Open', 'Closed', 'Archived')", name='ck_fp_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False) 
    status: Mapped[str] = mapped_column(String(10), nullable=False, default='Open')
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_adjustment: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    fiscal_year: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="fiscal_periods")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    journal_entries: Mapped[List["JournalEntry"]] = relationship(back_populates="fiscal_period") # type: ignore
    budget_details: Mapped[List["BudgetDetail"]] = relationship(back_populates="fiscal_period") # type: ignore

```

# app/models/accounting/tax_code.py
```py
# File: app/models/accounting/tax_code.py
# (Moved from app/models/tax_code.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List # Added List
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.core.user import User

class TaxCode(Base, TimestampMixin):
    __tablename__ = 'tax_codes'
    __table_args__ = (
        CheckConstraint("tax_type IN ('GST', 'Income Tax', 'Withholding Tax')", name='ck_tax_codes_tax_type'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False) 
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    affects_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    affects_account: Mapped[Optional["Account"]] = relationship("Account", back_populates="tax_code_applications", foreign_keys=[affects_account_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

    # Relationship defined by other models via back_populates:
    # journal_entry_lines: Mapped[List["JournalEntryLine"]]
    # product_default_tax_codes: Mapped[List["Product"]]

# Add to Account model:
Account.tax_code_applications = relationship("TaxCode", back_populates="affects_account", foreign_keys=[TaxCode.affects_account_id]) # type: ignore

```

# app/models/accounting/dimension.py
```py
# File: app/models/accounting/dimension.py
# New model for accounting.dimensions
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
# from app.models.core.user import User # For FKs
from typing import List, Optional

class Dimension(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'dimensions'
    __table_args__ = (
        UniqueConstraint('dimension_type', 'code', name='uq_dimensions_type_code'),
        {'schema': 'accounting'} 
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dimension_type: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    
    parent: Mapped[Optional["Dimension"]] = relationship("Dimension", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Dimension"]] = relationship("Dimension", back_populates="parent")

```

# app/models/accounting/account_type.py
```py
# File: app/models/accounting/account_type.py
# (Moved from app/models/account_type.py and fields updated)
from sqlalchemy import Column, Integer, String, Boolean, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin 
from typing import Optional

class AccountType(Base, TimestampMixin): 
    __tablename__ = 'account_types'
    __table_args__ = (
        CheckConstraint("category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_account_types_category'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False) 
    is_debit_balance: Mapped[bool] = mapped_column(Boolean, nullable=False)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False) 
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

```

# app/models/accounting/recurring_pattern.py
```py
# File: app/models/accounting/recurring_pattern.py
# (Moved from app/models/recurring_pattern.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional, List # Added List
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.journal_entry import JournalEntry # For relationship type hint
from app.models.core.user import User

class RecurringPattern(Base, TimestampMixin):
    __tablename__ = 'recurring_patterns'
    __table_args__ = (
        CheckConstraint("frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')", name='ck_recurring_patterns_frequency'),
        CheckConstraint("day_of_month BETWEEN 1 AND 31", name='ck_recurring_patterns_day_of_month'),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name='ck_recurring_patterns_day_of_week'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=False)
    
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    last_generated_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    next_generation_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    template_journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", foreign_keys=[template_entry_id], back_populates="template_for_patterns")
    generated_journal_entries: Mapped[List["JournalEntry"]] = relationship("JournalEntry", foreign_keys="JournalEntry.recurring_pattern_id", back_populates="generated_from_pattern")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/accounting/currency.py
```py
# File: app/models/accounting/currency.py
# (Moved from app/models/currency.py and fields updated)
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.core.user import User 
from typing import Optional

class Currency(Base, TimestampMixin):
    __tablename__ = 'currencies'
    __table_args__ = {'schema': 'accounting'}

    code: Mapped[str] = mapped_column(String(3), primary_key=True) 
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    format_string: Mapped[str] = mapped_column(String(20), default='#,##0.00') 

    created_by_user_id: Mapped[Optional[int]] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=True)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True)

    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/reporting/financial_statement_generator.py
```py
# File: app/reporting/financial_statement_generator.py
from typing import List, Dict, Any, Optional
from datetime import date, timedelta # Added timedelta
from decimal import Decimal

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.tax_service import TaxCodeService # Keep for GST F5 method
from app.services.core_services import CompanySettingsService # Keep for GST F5 method
from app.services.accounting_services import AccountTypeService
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 
from app.models.accounting.journal_entry import JournalEntryLine # New import

class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService, # Keep even if not used by GL directly, may be used by other reports
                 account_type_service: AccountTypeService, 
                 tax_code_service: Optional[TaxCodeService] = None, 
                 company_settings_service: Optional[CompanySettingsService] = None
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    async def _get_account_type_map(self) -> Dict[str, AccountType]:
        if self._account_type_map_cache is None:
             ats = await self.account_type_service.get_all()
             self._account_type_map_cache = {at.category: at for at in ats} # Assuming at.category is the key 'Asset', 'Liability' etc.
        return self._account_type_map_cache

    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        # ... (existing method, no changes needed for this step)
        result_list = []
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date)
            display_balance = balance_value 
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_balance = -balance_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_balance})
        return result_list

    async def _calculate_account_period_activity_for_report(self, accounts: List[Account], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        # ... (existing method, no changes needed for this step)
        result_list = []
        acc_type_map = await self._get_account_type_map() # Ensure map is loaded
        for account in accounts:
            activity_value = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            display_activity = activity_value
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            # For P&L: Revenue (credit nature) activity is usually shown positive if it increases profit.
            # Expense (debit nature) activity is usually shown positive.
            # Our get_account_balance_for_period returns net change (Debit-Credit).
            # Revenue: Credit > Debit => negative result => show positive.
            # Expense: Debit > Credit => positive result => show positive.
            if not is_debit_nature: # Revenue, Liability, Equity
                display_activity = -activity_value # Invert for typical P&L presentation of revenue
            
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_activity})
        return result_list

    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, include_zero_balances: bool = False) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step)
        accounts = await self.account_service.get_all_active()
        assets_orm = [a for a in accounts if a.account_type == 'Asset']
        liabilities_orm = [a for a in accounts if a.account_type == 'Liability']
        equity_orm = [a for a in accounts if a.account_type == 'Equity']
        asset_accounts = await self._calculate_account_balances_for_report(assets_orm, as_of_date)
        liability_accounts = await self._calculate_account_balances_for_report(liabilities_orm, as_of_date)
        equity_accounts = await self._calculate_account_balances_for_report(equity_orm, as_of_date)
        comp_asset_accs, comp_liab_accs, comp_equity_accs = None, None, None
        if comparative_date:
            comp_asset_accs = await self._calculate_account_balances_for_report(assets_orm, comparative_date)
            comp_liab_accs = await self._calculate_account_balances_for_report(liabilities_orm, comparative_date)
            comp_equity_accs = await self._calculate_account_balances_for_report(equity_orm, comparative_date)
        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != Decimal(0)]; liability_accounts = [a for a in liability_accounts if a['balance'] != Decimal(0)]; equity_accounts = [a for a in equity_accounts if a['balance'] != Decimal(0)]
            if comparative_date:
                comp_asset_accs = [a for a in comp_asset_accs if a['balance'] != Decimal(0)] if comp_asset_accs else None; comp_liab_accs = [a for a in comp_liab_accs if a['balance'] != Decimal(0)] if comp_liab_accs else None; comp_equity_accs = [a for a in comp_equity_accs if a['balance'] != Decimal(0)] if comp_equity_accs else None
        total_assets = sum(a['balance'] for a in asset_accounts); total_liabilities = sum(a['balance'] for a in liability_accounts); total_equity = sum(a['balance'] for a in equity_accounts)
        comp_total_assets = sum(a['balance'] for a in comp_asset_accs) if comp_asset_accs else None; comp_total_liabilities = sum(a['balance'] for a in comp_liab_accs) if comp_liab_accs else None; comp_total_equity = sum(a['balance'] for a in comp_equity_accs) if comp_equity_accs else None
        return {'title': 'Balance Sheet', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date, 'comparative_date': comparative_date,'assets': {'accounts': asset_accounts, 'total': total_assets, 'comparative_accounts': comp_asset_accs, 'comparative_total': comp_total_assets},'liabilities': {'accounts': liability_accounts, 'total': total_liabilities, 'comparative_accounts': comp_liab_accs, 'comparative_total': comp_total_liabilities},'equity': {'accounts': equity_accounts, 'total': total_equity, 'comparative_accounts': comp_equity_accs, 'comparative_total': comp_total_equity},'total_liabilities_equity': total_liabilities + total_equity,'comparative_total_liabilities_equity': (comp_total_liabilities + comp_total_equity) if comparative_date and comp_total_liabilities is not None and comp_total_equity is not None else None,'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")}

    async def generate_profit_loss(self, start_date: date, end_date: date, comparative_start: Optional[date] = None, comparative_end: Optional[date] = None) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step, but ensure _calculate_account_period_activity_for_report is correct)
        accounts = await self.account_service.get_all_active()
        revenues_orm = [a for a in accounts if a.account_type == 'Revenue']
        expenses_orm = [a for a in accounts if a.account_type == 'Expense'] 
        revenue_accounts = await self._calculate_account_period_activity_for_report(revenues_orm, start_date, end_date)
        expense_accounts = await self._calculate_account_period_activity_for_report(expenses_orm, start_date, end_date)
        comp_rev_accs, comp_exp_accs = None, None
        if comparative_start and comparative_end:
            comp_rev_accs = await self._calculate_account_period_activity_for_report(revenues_orm, comparative_start, comparative_end)
            comp_exp_accs = await self._calculate_account_period_activity_for_report(expenses_orm, comparative_start, comparative_end)
        total_revenue = sum(a['balance'] for a in revenue_accounts); total_expenses = sum(a['balance'] for a in expense_accounts) 
        net_profit = total_revenue - total_expenses
        comp_total_revenue = sum(a['balance'] for a in comp_rev_accs) if comp_rev_accs else None; comp_total_expenses = sum(a['balance'] for a in comp_exp_accs) if comp_exp_accs else None
        comp_net_profit = (comp_total_revenue - comp_total_expenses) if comp_total_revenue is not None and comp_total_expenses is not None else None
        return {'title': 'Profit & Loss Statement', 'report_date_description': f"For the period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'start_date': start_date, 'end_date': end_date, 'comparative_start': comparative_start, 'comparative_end': comparative_end,'revenue': {'accounts': revenue_accounts, 'total': total_revenue, 'comparative_accounts': comp_rev_accs, 'comparative_total': comp_total_revenue},'expenses': {'accounts': expense_accounts, 'total': total_expenses, 'comparative_accounts': comp_exp_accs, 'comparative_total': comp_total_expenses},'net_profit': net_profit, 'comparative_net_profit': comp_net_profit}

    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step)
        accounts = await self.account_service.get_all_active(); debit_accounts_list, credit_accounts_list = [], []; total_debits_val, total_credits_val = Decimal(0), Decimal(0) 
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue
            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if is_debit_nature: 
                if raw_balance >= Decimal(0): debit_accounts_list.append(account_data); total_debits_val += raw_balance
                else: account_data['balance'] = abs(raw_balance); credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
            else: 
                if raw_balance <= Decimal(0): credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
                else: account_data['balance'] = raw_balance; debit_accounts_list.append(account_data); total_debits_val += raw_balance
        debit_accounts_list.sort(key=lambda a: a['code']); credit_accounts_list.sort(key=lambda a: a['code'])
        return {'title': 'Trial Balance', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date,'debit_accounts': debit_accounts_list, 'credit_accounts': credit_accounts_list,'total_debits': total_debits_val, 'total_credits': total_credits_val,'is_balanced': abs(total_debits_val - total_credits_val) < Decimal("0.01")}

    async def generate_income_tax_computation(self, year_int_value: int) -> Dict[str, Any]: 
        # ... (existing method, no changes needed for this step)
        fiscal_year_obj: Optional[FiscalYear] = await self.fiscal_period_service.get_fiscal_year(year_int_value) # This method needs review in FiscalPeriodService
        if not fiscal_year_obj: raise ValueError(f"Fiscal year definition for {year_int_value} not found.")
        start_date, end_date = fiscal_year_obj.start_date, fiscal_year_obj.end_date
        pl_data = await self.generate_profit_loss(start_date, end_date); net_profit = pl_data['net_profit']
        adjustments = []; tax_effect = Decimal(0)
        tax_adj_accounts = await self.account_service.get_accounts_by_tax_treatment('Tax Adjustment')
        for account in tax_adj_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if abs(activity) < Decimal("0.01"): continue
            adj_is_addition = activity > Decimal(0) if account.account_type == 'Expense' else activity < Decimal(0)
            adjustments.append({'id': account.id, 'code': account.code, 'name': account.name, 'amount': activity, 'is_addition': adj_is_addition})
            tax_effect += activity 
        taxable_income = net_profit + tax_effect
        return {'title': f'Income Tax Computation for Year of Assessment {year_int_value + 1}', 'report_date_description': f"For Financial Year Ended {fiscal_year_obj.end_date.strftime('%d %b %Y')}",'year': year_int_value, 'fiscal_year_start': start_date, 'fiscal_year_end': end_date,'net_profit': net_profit, 'adjustments': adjustments, 'tax_effect': tax_effect, 'taxable_income': taxable_income}

    async def generate_gst_f5(self, start_date: date, end_date: date) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step)
        if not self.company_settings_service or not self.tax_code_service: raise RuntimeError("TaxCodeService and CompanySettingsService are required for GST F5.")
        company = await self.company_settings_service.get_company_settings();
        if not company: raise ValueError("Company settings not found.")
        report_data: Dict[str, Any] = {'title': f"GST F5 Return for period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'company_name': company.company_name,'gst_registration_no': company.gst_registration_no,'period_start': start_date, 'period_end': end_date,'standard_rated_supplies': Decimal(0), 'zero_rated_supplies': Decimal(0),'exempt_supplies': Decimal(0), 'total_supplies': Decimal(0),'taxable_purchases': Decimal(0), 'output_tax': Decimal(0),'input_tax': Decimal(0), 'tax_adjustments': Decimal(0), 'tax_payable': Decimal(0)}
        entries = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)
        for entry in entries:
            for line in entry.lines: 
                if not line.tax_code or not line.account: continue
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                line_net_amount = (line.debit_amount if line.debit_amount > Decimal(0) else line.credit_amount) # Assumes one is zero
                tax_on_line = line.tax_amount if line.tax_amount is not None else Decimal(0)
                if line.account.account_type == 'Revenue':
                    if tax_code_info.code == 'SR': report_data['standard_rated_supplies'] += line_net_amount; report_data['output_tax'] += tax_on_line
                    elif tax_code_info.code == 'ZR': report_data['zero_rated_supplies'] += line_net_amount
                    elif tax_code_info.code == 'ES': report_data['exempt_supplies'] += line_net_amount
                elif line.account.account_type in ['Expense', 'Asset']:
                    if tax_code_info.code == 'TX': report_data['taxable_purchases'] += line_net_amount; report_data['input_tax'] += tax_on_line
                    elif tax_code_info.code == 'BL': report_data['taxable_purchases'] += line_net_amount # Tax on BL is not claimed
        report_data['total_supplies'] = (report_data['standard_rated_supplies'] + report_data['zero_rated_supplies'] + report_data['exempt_supplies'])
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        return report_data

    # --- NEW Method for General Ledger ---
    async def generate_general_ledger(self, account_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        account_orm = await self.account_service.get_by_id(account_id)
        if not account_orm:
            raise ValueError(f"Account with ID {account_id} not found.")

        # Opening balance is balance as of (start_date - 1 day)
        ob_date = start_date - timedelta(days=1)
        opening_balance = await self.journal_service.get_account_balance(account_id, ob_date)

        # Fetch transactions for the period
        lines: List[JournalEntryLine] = await self.journal_service.get_posted_lines_for_account_in_range(
            account_id, start_date, end_date
        )

        transactions_data = []
        current_balance = opening_balance
        for line in lines:
            if not line.journal_entry: # Should not happen with joinedload
                continue 
            
            movement = line.debit_amount - line.credit_amount
            current_balance += movement
            
            transactions_data.append({
                "date": line.journal_entry.entry_date,
                "entry_no": line.journal_entry.entry_no,
                "je_description": line.journal_entry.description or "",
                "line_description": line.description or "",
                "debit": line.debit_amount,
                "credit": line.credit_amount,
                "balance": current_balance
            })
        
        closing_balance = current_balance

        return {
            "title": "General Ledger",
            "report_date_description": f"For Account: {account_orm.code} - {account_orm.name} from {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
            "account_code": account_orm.code,
            "account_name": account_orm.name,
            "start_date": start_date,
            "end_date": end_date,
            "opening_balance": opening_balance,
            "transactions": transactions_data,
            "closing_balance": closing_balance
        }

```

# app/reporting/__init__.py
```py
# File: app/reporting/__init__.py
# (Content as previously generated, verified)
from .financial_statement_generator import FinancialStatementGenerator
from .tax_report_generator import TaxReportGenerator
from .report_engine import ReportEngine

__all__ = [
    "FinancialStatementGenerator",
    "TaxReportGenerator",
    "ReportEngine",
]

```

# app/reporting/report_engine.py
```py
# File: app/reporting/report_engine.py
from typing import Dict, Any, Literal, List, Optional, TYPE_CHECKING 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepInFrame
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm 
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
from decimal import Decimal, InvalidOperation
from datetime import date

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class ReportEngine:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(name='ReportTitle', parent=self.styles['h1'], alignment=TA_CENTER, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='ReportSubTitle', parent=self.styles['h2'], alignment=TA_CENTER, fontSize=12, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='SectionHeader', parent=self.styles['h3'], fontSize=11, spaceBefore=0.2*inch, spaceAfter=0.1*inch, textColor=colors.HexColor("#2F5496")))
        self.styles.add(ParagraphStyle(name='AccountName', parent=self.styles['Normal'], leftIndent=0.2*inch))
        self.styles.add(ParagraphStyle(name='AccountNameBold', parent=self.styles['AccountName'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='Amount', parent=self.styles['Normal'], alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle(name='AmountBold', parent=self.styles['Amount'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName='Helvetica-Bold', alignment=TA_CENTER))
        self.styles.add(ParagraphStyle(name='Footer', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=8))


    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes:
        title = report_data.get('title', "Financial Report")
        if format_type == "pdf":
            if title == "Balance Sheet":
                return await self._export_balance_sheet_to_pdf(report_data)
            elif title == "Profit & Loss Statement":
                return await self._export_profit_loss_to_pdf(report_data)
            else: # Fallback for TB, GL etc.
                return self._export_generic_table_to_pdf(report_data)
        elif format_type == "excel":
            if title == "Balance Sheet":
                return await self._export_balance_sheet_to_excel(report_data)
            elif title == "Profit & Loss Statement":
                return await self._export_profit_loss_to_excel(report_data)
            else: # Fallback for TB, GL etc.
                return self._export_generic_table_to_excel(report_data)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2, show_blank_for_zero: bool = False) -> str:
        if value is None: return "" if show_blank_for_zero else "0.00"
        if not isinstance(value, Decimal): 
            try: value = Decimal(str(value))
            except InvalidOperation: return "ERR_DEC" 
        if show_blank_for_zero and value.is_zero(): return ""
        return f"{value:,.{places}f}"

    async def _get_company_name(self) -> str:
        settings = await self.app_core.company_settings_service.get_company_settings()
        return settings.company_name if settings else "Your Company"

    def _add_pdf_header_footer(self, canvas, doc, company_name: str, report_title: str, date_desc: str):
        canvas.saveState()
        # Header
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin - 0.5*inch, company_name)
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin - 0.75*inch, report_title)
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin - 1.0*inch, date_desc)
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.drawString(doc.leftMargin, 0.5*inch, f"Generated on: {date.today().strftime('%d %b %Y')}")
        canvas.drawRightString(doc.width + doc.leftMargin - 0.1*inch, 0.5*inch, f"Page {doc.page}")
        canvas.restoreState()

    # --- Balance Sheet Specific PDF ---
    async def _export_balance_sheet_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        company_name = await self._get_company_name()
        report_title = report_data.get('title', "Balance Sheet")
        date_desc = report_data.get('report_date_description', "")

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=1.25*inch, bottomMargin=0.75*inch)
        
        story: List[Any] = []
        has_comparative = bool(report_data.get('comparative_date'))
        
        col_widths = [3.5*inch, 1.5*inch]
        if has_comparative: col_widths.append(1.5*inch)

        header_texts = ["Description", "Current Period"]
        if has_comparative: header_texts.append("Comparative")
        
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]
        
        # Helper to build BS table data
        def build_section_data(section_key: str, title: str):
            data: List[List[Any]] = []
            section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""])) # Span title
            
            for acc in section.get('accounts', []):
                row = [Paragraph(f"{acc['code']} - {acc['name']}", self.styles['AccountName']),
                       Paragraph(self._format_decimal(acc['balance']), self.styles['Amount'])]
                if has_comparative:
                    comp_bal_str = self._format_decimal(acc.get('comparative_balance')) if section.get('comparative_accounts') and \
                                   next((ca for ca in section['comparative_accounts'] if ca['id'] == acc['id']), {}).get('balance') is not None else "" # More robust comparative access
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)

            total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']),
                         Paragraph(self._format_decimal(section.get('total')), self.styles['AmountBold'])]
            if has_comparative:
                total_row.append(Paragraph(self._format_decimal(section.get('comparative_total')), self.styles['AmountBold']))
            data.append(total_row)
            data.append([Spacer(1, 0.1*inch)] * len(col_widths)) # Spacer row
            return data

        bs_data: List[List[Any]] = [table_header_row]
        bs_data.extend(build_section_data('assets', 'Assets'))
        bs_data.extend(build_section_data('liabilities', 'Liabilities'))
        bs_data.extend(build_section_data('equity', 'Equity'))
        
        # Total Liabilities & Equity
        total_lia_eq_row = [Paragraph("Total Liabilities & Equity", self.styles['AccountNameBold']),
                             Paragraph(self._format_decimal(report_data.get('total_liabilities_equity')), self.styles['AmountBold'])]
        if has_comparative:
            total_lia_eq_row.append(Paragraph(self._format_decimal(report_data.get('comparative_total_liabilities_equity')), self.styles['AmountBold']))
        bs_data.append(total_lia_eq_row)
        
        bs_table = Table(bs_data, colWidths=col_widths)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEABOVE', (0, -1), (-1,-1), 1, colors.black), # Line above Total L+E
            ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), # Double underline for totals
            ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),
        ])
        # Spanning section headers
        current_row_idx = 1 # After table header
        for section_key in ['assets', 'liabilities', 'equity']:
            if section_key in report_data:
                style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx)) # Span the section title
                current_row_idx += len(report_data[section_key].get('accounts', [])) + 2 # accounts + total row + spacer

        bs_table.setStyle(style)
        story.append(bs_table)
        
        if report_data.get('is_balanced') is False:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Warning: Balance Sheet is out of balance!", 
                                   ParagraphStyle(name='Warning', parent=self.styles['Normal'], textColor=colors.red, fontName='Helvetica-Bold')))

        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), 
                         onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc))
        return buffer.getvalue()

    # --- Profit & Loss Specific PDF ---
    async def _export_profit_loss_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        company_name = await self._get_company_name()
        report_title = report_data.get('title', "Profit & Loss Statement")
        date_desc = report_data.get('report_date_description', "")

        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []
        has_comparative = bool(report_data.get('comparative_start'))
        
        col_widths = [3.5*inch, 1.5*inch]
        if has_comparative: col_widths.append(1.5*inch)

        header_texts = ["Description", "Current Period"]
        if has_comparative: header_texts.append("Comparative")
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]

        def build_pl_section_data(section_key: str, title: str, is_subtraction: bool = False):
            data: List[List[Any]] = []
            section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""]))
            
            for acc in section.get('accounts', []):
                balance = acc['balance']
                # Expenses are typically positive in P&L, revenue positive. Generator ensures this.
                row = [Paragraph(f"{acc['code']} - {acc['name']}", self.styles['AccountName']),
                       Paragraph(self._format_decimal(balance), self.styles['Amount'])]
                if has_comparative:
                    comp_acc = next((ca for ca in section.get('comparative_accounts', []) if ca['id'] == acc['id']), None)
                    comp_bal_str = self._format_decimal(comp_acc['balance']) if comp_acc else ""
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)

            total = section.get('total')
            total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']),
                         Paragraph(self._format_decimal(total), self.styles['AmountBold'])]
            if has_comparative:
                comp_total = section.get('comparative_total')
                total_row.append(Paragraph(self._format_decimal(comp_total), self.styles['AmountBold']))
            data.append(total_row)
            data.append([Spacer(1, 0.1*inch)] * len(col_widths))
            return data, total, section.get('comparative_total') if has_comparative else None

        pl_data: List[List[Any]] = [table_header_row]
        
        rev_data, total_revenue, comp_total_revenue = build_pl_section_data('revenue', 'Revenue')
        pl_data.extend(rev_data)

        # Assuming Cost of Sales could be a section. If not, FinancialStatementGenerator needs to provide it.
        # For now, let's proceed as if only revenue and expenses are top-level sections for accounts.
        
        exp_data, total_expenses, comp_total_expenses = build_pl_section_data('expenses', 'Operating Expenses', is_subtraction=True)
        pl_data.extend(exp_data)
        
        # Net Profit
        net_profit = report_data.get('net_profit', Decimal(0))
        comp_net_profit = report_data.get('comparative_net_profit')

        net_profit_row = [Paragraph("Net Profit / (Loss)", self.styles['AccountNameBold']),
                          Paragraph(self._format_decimal(net_profit), self.styles['AmountBold'])]
        if has_comparative:
            net_profit_row.append(Paragraph(self._format_decimal(comp_net_profit), self.styles['AmountBold']))
        pl_data.append(net_profit_row)

        pl_table = Table(pl_data, colWidths=col_widths)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEABOVE', (1, -1), (-1,-1), 1, colors.black), # Line above Net Profit
            ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), # Double underline for Net Profit
            ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),
        ])
        # Dynamic spanning for section headers (similar to BS)
        current_row_idx = 1
        for section_key in ['revenue', 'expenses']: # Add more if generator provides (e.g. cost_of_sales)
            if section_key in report_data:
                style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx))
                current_row_idx += len(report_data[section_key].get('accounts', [])) + 2

        pl_table.setStyle(style)
        story.append(pl_table)

        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), 
                         onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc))
        return buffer.getvalue()

    # --- Generic PDF Exporter (for TB, GL) ---
    def _export_generic_table_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        # This is the original _export_to_pdf_generic, slightly refactored
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4) if report_data.get("title") == "General Ledger" else A4,
                                rightMargin=0.5*inch, leftMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        story: List[Any] = [] 

        story.append(Paragraph(report_data.get('title', "Report"), self.styles['h1']))
        if report_data.get('report_date_description'):
            story.append(Paragraph(report_data.get('report_date_description'), self.styles['h3']))
        story.append(Spacer(1, 0.2*inch))
        
        table_data: List[List[Any]] = []
        # ... (Logic from existing _export_to_pdf_generic for TB/GL data extraction) ...
        # For Trial Balance:
        if 'debit_accounts' in report_data:
            table_data.append([Paragraph(h, self.styles['TableHeader']) for h in ["Account Code", "Account Name", "Debit", "Credit"]])
            for acc in report_data.get('debit_accounts', []):
                table_data.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                table_data.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            table_data.append(["", Paragraph("TOTALS", self.styles['AccountNameBold']), 
                               Paragraph(self._format_decimal(report_data.get('total_debits')), self.styles['AmountBold']), 
                               Paragraph(self._format_decimal(report_data.get('total_credits')), self.styles['AmountBold'])])
        # For General Ledger:
        elif 'transactions' in report_data:
            table_data.append([Paragraph(h, self.styles['TableHeader']) for h in ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]])
            table_data.append(["", "", Paragraph("Opening Balance", self.styles['AccountNameBold']), "", "", Paragraph(self._format_decimal(report_data.get('opening_balance')), self.styles['AmountBold'])])
            for txn in report_data.get('transactions', []):
                 table_data.append([
                    txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else str(txn['date']),
                    txn['entry_no'], Paragraph(txn.get('je_description','')[:50] + (" // " + txn.get('line_description','')[:50] if txn.get('line_description') else ""), self.styles['Normal']), # Keep description concise
                    self._format_decimal(txn['debit'], show_blank_for_zero=True), 
                    self._format_decimal(txn['credit'], show_blank_for_zero=True), 
                    self._format_decimal(txn['balance'])
                ])
            table_data.append(["", "", Paragraph("Closing Balance", self.styles['AccountNameBold']), "", "", Paragraph(self._format_decimal(report_data.get('closing_balance')), self.styles['AmountBold'])])


        if table_data:
            num_cols = len(table_data[0])
            col_widths_generic = [doc.width/num_cols]*num_cols
            if report_data.get("title") == "General Ledger" and num_cols == 6:
                col_widths_generic = [0.8*inch, 1*inch,landscape(A4)[0] - 0.5*inch*2 - (0.8+1+1+1+1)*inch, 1*inch, 1*inch, 1*inch]


            table = Table(table_data, colWidths=col_widths_generic)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (3,1), (-1,-1), 'RIGHT'), # Numerical columns alignment for GL/TB
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No data to display for this report.", self.styles['Normal']))

        doc.build(story)
        return buffer.getvalue()

    # --- Excel Export Methods ---
    def _apply_excel_header_style(self, cell, bold=True, size=12, alignment='center'):
        cell.font = Font(bold=bold, size=size)
        if alignment == 'center': cell.alignment = Alignment(horizontal='center', vertical='center')
        elif alignment == 'right': cell.alignment = Alignment(horizontal='right', vertical='center')
        else: cell.alignment = Alignment(horizontal='left', vertical='center')

    def _apply_excel_amount_style(self, cell, bold=False):
        cell.number_format = '#,##0.00;[Red](#,##0.00)' # Basic accounting format
        cell.alignment = Alignment(horizontal='right')
        if bold: cell.font = Font(bold=True)
        
    async def _export_balance_sheet_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Balance Sheet"
        company_name = await self._get_company_name()
        has_comparative = bool(report_data.get('comparative_date'))

        row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False)
        row_num += 2

        headers = ["Description", "Current Period"]
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='left' if col==1 else 'center')
        row_num +=1

        def write_section(section_key: str, title: str):
            nonlocal row_num
            section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496")
            row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'])))
                if has_comparative:
                    comp_acc = next((ca for ca in section.get('comparative_accounts', []) if ca['id'] == acc['id']), None)
                    comp_val = float(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else None
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True)
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True)
            ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'))
            if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'))
            row_num += 2

        write_section('assets', 'Assets')
        write_section('liabilities', 'Liabilities')
        write_section('equity', 'Equity')
        
        ws.cell(row=row_num, column=1, value="Total Liabilities & Equity").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('total_liabilities_equity',0))), bold=True)
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_total_liabilities_equity',0))), bold=True)
        ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'), double='double') # Double underline final total
        if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'), bottom=Side(style='double'))
        row_num +=1

        if report_data.get('is_balanced') is False:
            ws.cell(row=row_num, column=1, value="Warning: Balance Sheet out of balance!").font = Font(color="FF0000", bold=True)
        
        for i, col_letter in enumerate(['A','B','C'][:len(headers)]):
            ws.column_dimensions[col_letter].width = 40 if i==0 else 20

        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    async def _export_profit_loss_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Profit and Loss"
        company_name = await self._get_company_name()
        has_comparative = bool(report_data.get('comparative_start'))

        row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False)
        row_num += 2

        headers = ["Description", "Current Period"]
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='left' if col==1 else 'center')
        row_num +=1
        
        def write_pl_section(section_key: str, title: str):
            nonlocal row_num
            section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496")
            row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'])))
                if has_comparative:
                    comp_acc = next((ca for ca in section.get('comparative_accounts', []) if ca['id'] == acc['id']), None)
                    comp_val = float(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else None
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True)
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True)
            ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'))
            if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'))
            row_num +=1
            return section.get('total', Decimal(0)), section.get('comparative_total') if has_comparative else Decimal(0)

        total_revenue, comp_total_revenue = write_pl_section('revenue', 'Revenue')
        # Handle Cost of Sales and Gross Profit if structure supports it, for now directly to expenses
        row_num +=1 # Spacer
        total_expenses, comp_total_expenses = write_pl_section('expenses', 'Operating Expenses')
        row_num +=1 # Spacer

        ws.cell(row=row_num, column=1, value="Net Profit / (Loss)").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('net_profit',0))), bold=True)
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_net_profit',0))), bold=True)
        ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'), bottom=Side(style='double'))
        if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'), bottom=Side(style='double'))

        for i, col_letter in enumerate(['A','B','C'][:len(headers)]):
            ws.column_dimensions[col_letter].width = 40 if i==0 else 20

        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    # --- Generic Excel Exporter (for TB, GL) ---
    def _export_generic_table_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        # This is the original _export_to_excel_generic, slightly refactored
        wb = openpyxl.Workbook()
        ws = wb.active 
        ws.title = report_data.get('title', "Report")[:30] # type: ignore

        row_num = 1
        ws.cell(row=row_num, column=1, value=report_data.get('title')).font = Font(bold=True, size=14) # type: ignore
        row_num += 1
        if report_data.get('report_date_description'):
            ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')).font = Font(italic=True) # type: ignore
            row_num += 1
        row_num += 1 

        # ... (Logic from existing _export_to_excel_generic for TB/GL data extraction) ...
        if 'debit_accounts' in report_data:
            headers = ["Account Code", "Account Name", "Debit", "Credit"]
            for col, header_text in enumerate(headers,1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col>1 else 'left')
            row_num+=1
            for acc in report_data.get('debit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name'])
                self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(acc['balance'])))
                row_num+=1
            for acc in report_data.get('credit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name'])
                self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(acc['balance'])))
                row_num+=1
            row_num+=1
            ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits',0))), bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits',0))), bold=True)
        elif 'transactions' in report_data: # General Ledger
            headers = ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]
            for col, header_text in enumerate(headers,1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col > 2 else 'left')
            row_num+=1
            ws.cell(row=row_num, column=3, value="Opening Balance").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(report_data.get('opening_balance',0))), bold=True)
            row_num+=1
            for txn in report_data.get('transactions',[]):
                ws.cell(row=row_num, column=1, value=txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else txn['date'])
                ws.cell(row=row_num, column=2, value=txn['entry_no'])
                ws.cell(row=row_num, column=3, value=txn.get('je_description','') + (" // " + txn.get('line_description','') if txn.get('line_description') else ""))
                self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(txn['debit'] if txn['debit'] else 0)))
                self._apply_excel_amount_style(ws.cell(row=row_num, column=5, value=float(txn['credit'] if txn['credit'] else 0)))
                self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(txn['balance'])))
                row_num+=1
            ws.cell(row=row_num, column=3, value="Closing Balance").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(report_data.get('closing_balance',0))), bold=True)
            
        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = 15 # Default width
            if col_idx == 3 and 'transactions' in report_data: # Description for GL
                 ws.column_dimensions[column_letter].width = 50
            elif col_idx == 2 and 'debit_accounts' in report_data: # Account Name for TB
                 ws.column_dimensions[column_letter].width = 40

        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()


```

# app/reporting/tax_report_generator.py
```py
# File: app/reporting/tax_report_generator.py
from typing import TYPE_CHECKING # Added TYPE_CHECKING
from datetime import date 

# from app.core.application_core import ApplicationCore # Removed direct import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class TaxReportGenerator:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal for ApplicationCore
        self.app_core = app_core
        # Services would be accessed via self.app_core if needed, e.g., self.app_core.journal_service
        print("TaxReportGenerator initialized (stub).")

    async def generate_gst_audit_file(self, start_date: date, end_date: date):
        print(f"Generating GST Audit File for {start_date} to {end_date} (stub).")
        # Example access: company_name = (await self.app_core.company_settings_service.get_company_settings()).company_name
        return {"filename": "gst_audit.xlsx", "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data": b"dummy_excel_data"}

    async def generate_income_tax_schedules(self, fiscal_year_id: int):
        print(f"Generating Income Tax Schedules for fiscal year ID {fiscal_year_id} (stub).")
        return {"schedule_name": "Capital Allowances", "data": []}

```

# app/business_logic/vendor_manager.py
```py
# app/business_logic/vendor_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.vendor import Vendor
from app.services.business_services import VendorService
from app.services.account_service import AccountService # Corrected import
from app.services.accounting_services import CurrencyService # Correct import
from app.utils.result import Result
from app.utils.pydantic_models import VendorCreateData, VendorUpdateData, VendorSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class VendorManager:
    def __init__(self, 
                 vendor_service: VendorService, 
                 account_service: AccountService, 
                 currency_service: CurrencyService, 
                 app_core: "ApplicationCore"):
        self.vendor_service = vendor_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger 

    async def get_vendor_for_dialog(self, vendor_id: int) -> Optional[Vendor]:
        """ Fetches a full vendor ORM object for dialog population. """
        try:
            return await self.vendor_service.get_by_id(vendor_id)
        except Exception as e:
            self.logger.error(f"Error fetching vendor ID {vendor_id} for dialog: {e}", exc_info=True)
            return None

    async def get_vendors_for_listing(self, 
                                       active_only: bool = True,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[VendorSummaryData]]:
        """ Fetches a list of vendor summaries for table display. """
        try:
            summaries: List[VendorSummaryData] = await self.vendor_service.get_all_summary(
                active_only=active_only,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching vendor listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve vendor list: {str(e)}"])

    async def _validate_vendor_data(self, dto: VendorCreateData | VendorUpdateData, existing_vendor_id: Optional[int] = None) -> List[str]:
        """ Common validation logic for creating and updating vendors. """
        errors: List[str] = []

        if dto.vendor_code:
            existing_by_code = await self.vendor_service.get_by_code(dto.vendor_code)
            if existing_by_code and (existing_vendor_id is None or existing_by_code.id != existing_vendor_id):
                errors.append(f"Vendor code '{dto.vendor_code}' already exists.")
        else: 
            errors.append("Vendor code is required.") 
            
        if dto.name is None or not dto.name.strip(): 
            errors.append("Vendor name is required.")

        if dto.payables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.payables_account_id)
            if not acc:
                errors.append(f"Payables account ID '{dto.payables_account_id}' not found.")
            elif acc.account_type != 'Liability': 
                errors.append(f"Account '{acc.code} - {acc.name}' is not a Liability account and cannot be used as payables account.")
            elif not acc.is_active:
                 errors.append(f"Payables account '{acc.code} - {acc.name}' is not active.")

        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) 
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        else: 
             errors.append("Currency code is required.")
        return errors

    async def create_vendor(self, dto: VendorCreateData) -> Result[Vendor]:
        validation_errors = await self._validate_vendor_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            vendor_orm = Vendor(
                vendor_code=dto.vendor_code, name=dto.name, legal_name=dto.legal_name,
                uen_no=dto.uen_no, gst_registered=dto.gst_registered, gst_no=dto.gst_no,
                withholding_tax_applicable=dto.withholding_tax_applicable,
                withholding_tax_rate=dto.withholding_tax_rate,
                contact_person=dto.contact_person, email=str(dto.email) if dto.email else None, phone=dto.phone,
                address_line1=dto.address_line1, address_line2=dto.address_line2,
                postal_code=dto.postal_code, city=dto.city, country=dto.country,
                payment_terms=dto.payment_terms, currency_code=dto.currency_code, 
                is_active=dto.is_active, vendor_since=dto.vendor_since, notes=dto.notes,
                bank_account_name=dto.bank_account_name, bank_account_number=dto.bank_account_number,
                bank_name=dto.bank_name, bank_branch=dto.bank_branch, bank_swift_code=dto.bank_swift_code,
                payables_account_id=dto.payables_account_id,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_vendor = await self.vendor_service.save(vendor_orm)
            return Result.success(saved_vendor)
        except Exception as e:
            self.logger.error(f"Error creating vendor '{dto.vendor_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the vendor: {str(e)}"])

    async def update_vendor(self, vendor_id: int, dto: VendorUpdateData) -> Result[Vendor]:
        existing_vendor = await self.vendor_service.get_by_id(vendor_id)
        if not existing_vendor:
            return Result.failure([f"Vendor with ID {vendor_id} not found."])

        validation_errors = await self._validate_vendor_data(dto, existing_vendor_id=vendor_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_vendor, key):
                    if key == 'email' and value is not None: 
                        setattr(existing_vendor, key, str(value))
                    else:
                        setattr(existing_vendor, key, value)
            
            existing_vendor.updated_by_user_id = dto.user_id
            
            updated_vendor = await self.vendor_service.save(existing_vendor)
            return Result.success(updated_vendor)
        except Exception as e:
            self.logger.error(f"Error updating vendor ID {vendor_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the vendor: {str(e)}"])

    async def toggle_vendor_active_status(self, vendor_id: int, user_id: int) -> Result[Vendor]:
        vendor = await self.vendor_service.get_by_id(vendor_id)
        if not vendor:
            return Result.failure([f"Vendor with ID {vendor_id} not found."])
        
        vendor_name_for_log = vendor.name 
        
        vendor.is_active = not vendor.is_active
        vendor.updated_by_user_id = user_id

        try:
            updated_vendor = await self.vendor_service.save(vendor)
            action = "activated" if updated_vendor.is_active else "deactivated"
            self.logger.info(f"Vendor '{vendor_name_for_log}' (ID: {vendor_id}) {action} by user ID {user_id}.")
            return Result.success(updated_vendor)
        except Exception as e:
            self.logger.error(f"Error toggling active status for vendor ID {vendor_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for vendor: {str(e)}"])


```

# app/business_logic/__init__.py
```py
# File: app/business_logic/__init__.py
from .customer_manager import CustomerManager
from .vendor_manager import VendorManager
from .product_manager import ProductManager
from .sales_invoice_manager import SalesInvoiceManager
from .purchase_invoice_manager import PurchaseInvoiceManager 

__all__ = [
    "CustomerManager",
    "VendorManager",
    "ProductManager",
    "SalesInvoiceManager",
    "PurchaseInvoiceManager", 
]

```

# app/business_logic/sales_invoice_manager.py
```py
# app/business_logic/sales_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime 

from sqlalchemy.orm import selectinload 

from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.journal_entry import JournalEntry 

from app.services.business_services import SalesInvoiceService, CustomerService, ProductService
from app.services.core_services import SequenceService, ConfigurationService 
from app.services.tax_service import TaxCodeService 
from app.services.account_service import AccountService 

from app.utils.result import Result
from app.utils.pydantic_models import (
    SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData,
    SalesInvoiceSummaryData, TaxCalculationResultData,
    JournalEntryData, JournalEntryLineData 
)
from app.tax.tax_calculator import TaxCalculator 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class SalesInvoiceManager:
    def __init__(self, 
                 sales_invoice_service: SalesInvoiceService,
                 customer_service: CustomerService,
                 product_service: ProductService,
                 tax_code_service: TaxCodeService, 
                 tax_calculator: TaxCalculator, 
                 sequence_service: SequenceService,
                 account_service: AccountService, 
                 configuration_service: ConfigurationService, 
                 app_core: "ApplicationCore"):
        self.sales_invoice_service = sales_invoice_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.tax_code_service = tax_code_service
        self.tax_calculator = tax_calculator 
        self.sequence_service = sequence_service
        self.account_service = account_service 
        self.configuration_service = configuration_service 
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_and_prepare_invoice_data(
        self, 
        dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData],
        is_update: bool = False 
    ) -> Result[Dict[str, Any]]:
        errors: List[str] = []
        
        customer = await self.customer_service.get_by_id(dto.customer_id)
        if not customer:
            errors.append(f"Customer with ID {dto.customer_id} not found.")
        elif not customer.is_active:
            errors.append(f"Customer '{customer.name}' (ID: {dto.customer_id}) is not active.")

        if not dto.currency_code or len(dto.currency_code) != 3:
            errors.append(f"Invalid currency code: '{dto.currency_code}'.")
        else:
           currency_obj = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
           if not currency_obj or not currency_obj.is_active:
               errors.append(f"Currency '{dto.currency_code}' is invalid or not active.")

        calculated_lines_for_orm: List[Dict[str, Any]] = []
        invoice_subtotal_calc = Decimal(0)
        invoice_total_tax_calc = Decimal(0)

        if not dto.lines:
            errors.append("Sales invoice must have at least one line item.")
        
        for i, line_dto in enumerate(dto.lines):
            line_errors_current_line: List[str] = []
            product: Optional[Product] = None
            line_description = line_dto.description
            unit_price = line_dto.unit_price
            line_sales_account_id: Optional[int] = None 

            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product:
                    line_errors_current_line.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active:
                    line_errors_current_line.append(f"Product '{product.name}' is not active on line {i+1}.")
                
                if product: 
                    if not line_description: line_description = product.name
                    if (unit_price is None or unit_price == Decimal(0)) and product.sales_price is not None:
                        unit_price = product.sales_price
                    line_sales_account_id = product.sales_account_id 
            
            if not line_description: 
                line_errors_current_line.append(f"Description is required on line {i+1}.")

            if unit_price is None: 
                line_errors_current_line.append(f"Unit price is required on line {i+1}.")
                unit_price = Decimal(0) 

            try:
                qty = Decimal(str(line_dto.quantity))
                price = Decimal(str(unit_price)) 
                discount_pct = Decimal(str(line_dto.discount_percent))
                if qty <= 0: line_errors_current_line.append(f"Quantity must be positive on line {i+1}.")
                if price < 0: line_errors_current_line.append(f"Unit price cannot be negative on line {i+1}.")
                if not (0 <= discount_pct <= 100): line_errors_current_line.append(f"Discount percent must be between 0 and 100 on line {i+1}.")
            except InvalidOperation:
                line_errors_current_line.append(f"Invalid numeric value for quantity, price, or discount on line {i+1}.")
                errors.extend(line_errors_current_line)
                continue

            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            line_tax_amount_calc = Decimal(0)
            line_tax_account_id: Optional[int] = None 
            if line_dto.tax_code:
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(
                    amount=line_subtotal_before_tax,
                    tax_code_str=line_dto.tax_code,
                    transaction_type="SalesInvoiceLine" 
                )
                line_tax_amount_calc = tax_calc_result.tax_amount
                line_tax_account_id = tax_calc_result.tax_account_id 
                
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0): 
                    tc_check = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check or not tc_check.is_active:
                        line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            
            invoice_subtotal_calc += line_subtotal_before_tax
            invoice_total_tax_calc += line_tax_amount_calc
            
            if line_errors_current_line:
                errors.extend(line_errors_current_line)
            
            calculated_lines_for_orm.append({
                "product_id": line_dto.product_id, "description": line_description,
                "quantity": qty, "unit_price": price,
                "discount_percent": discount_pct,
                "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_subtotal": line_subtotal_before_tax.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "tax_code": line_dto.tax_code, "tax_amount": line_tax_amount_calc, 
                "line_total": (line_subtotal_before_tax + line_tax_amount_calc).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "dimension1_id": line_dto.dimension1_id, "dimension2_id": line_dto.dimension2_id,
                "_line_sales_account_id": line_sales_account_id,
                "_line_tax_account_id": line_tax_account_id 
            })

        if errors:
            return Result.failure(errors)

        invoice_grand_total = invoice_subtotal_calc + invoice_total_tax_calc

        return Result.success({
            "header_dto": dto, "customer_orm": customer, "calculated_lines_for_orm": calculated_lines_for_orm,
            "invoice_subtotal": invoice_subtotal_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_total_tax": invoice_total_tax_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_grand_total": invoice_grand_total.quantize(Decimal("0.01"), ROUND_HALF_UP),
        })

    async def create_draft_invoice(self, dto: SalesInvoiceCreateData) -> Result[SalesInvoice]:
        preparation_result = await self._validate_and_prepare_invoice_data(dto)
        if not preparation_result.is_success:
            return Result.failure(preparation_result.errors)
        
        prepared_data = preparation_result.value; assert prepared_data is not None 
        header_dto = cast(SalesInvoiceCreateData, prepared_data["header_dto"])

        try:
            invoice_no_val = await self.app_core.db_manager.execute_scalar( 
                 "SELECT core.get_next_sequence_value($1);", "sales_invoice"
            )
            if not invoice_no_val or not isinstance(invoice_no_val, str):
                 self.logger.error(f"Failed to generate invoice number from DB or unexpected return type: {invoice_no_val}")
                 return Result.failure(["Failed to generate invoice number."])
            invoice_no = invoice_no_val

            invoice_orm = SalesInvoice(
                invoice_no=invoice_no, customer_id=header_dto.customer_id,
                invoice_date=header_dto.invoice_date, due_date=header_dto.due_date,
                currency_code=header_dto.currency_code, exchange_rate=header_dto.exchange_rate,
                notes=header_dto.notes, terms_and_conditions=header_dto.terms_and_conditions,
                subtotal=prepared_data["invoice_subtotal"], tax_amount=prepared_data["invoice_total_tax"],
                total_amount=prepared_data["invoice_grand_total"], amount_paid=Decimal(0), 
                status=InvoiceStatusEnum.DRAFT.value,
                created_by_user_id=header_dto.user_id, updated_by_user_id=header_dto.user_id
            )
            for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                invoice_orm.lines.append(SalesInvoiceLine(line_number=i + 1, **orm_line_data))
            
            saved_invoice = await self.sales_invoice_service.save(invoice_orm)
            return Result.success(saved_invoice)
        except Exception as e:
            self.logger.error(f"Error creating draft sales invoice: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred creating sales invoice: {str(e)}"])

    async def update_draft_invoice(self, invoice_id: int, dto: SalesInvoiceUpdateData) -> Result[SalesInvoice]:
        async with self.app_core.db_manager.session() as session: 
            existing_invoice = await session.get(SalesInvoice, invoice_id, options=[selectinload(SalesInvoice.lines)])
            if not existing_invoice: return Result.failure([f"Sales Invoice ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only draft invoices can be updated. Current status: {existing_invoice.status}"])

            preparation_result = await self._validate_and_prepare_invoice_data(dto, is_update=True)
            if not preparation_result.is_success: return Result.failure(preparation_result.errors)

            prepared_data = preparation_result.value; assert prepared_data is not None 
            header_dto = cast(SalesInvoiceUpdateData, prepared_data["header_dto"])

            try:
                existing_invoice.customer_id = header_dto.customer_id; existing_invoice.invoice_date = header_dto.invoice_date
                existing_invoice.due_date = header_dto.due_date; existing_invoice.currency_code = header_dto.currency_code
                existing_invoice.exchange_rate = header_dto.exchange_rate; existing_invoice.notes = header_dto.notes
                existing_invoice.terms_and_conditions = header_dto.terms_and_conditions
                existing_invoice.subtotal = prepared_data["invoice_subtotal"]; existing_invoice.tax_amount = prepared_data["invoice_total_tax"]
                existing_invoice.total_amount = prepared_data["invoice_grand_total"]
                existing_invoice.updated_by_user_id = header_dto.user_id
                
                for line_orm_to_delete in list(existing_invoice.lines): await session.delete(line_orm_to_delete)
                await session.flush() 

                new_lines_orm: List[SalesInvoiceLine] = []
                for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                    orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                    new_lines_orm.append(SalesInvoiceLine(line_number=i + 1, **orm_line_data))
                existing_invoice.lines = new_lines_orm 
                
                await session.flush()
                await session.refresh(existing_invoice)
                if existing_invoice.lines:
                    await session.refresh(existing_invoice, attribute_names=['lines'])
                return Result.success(existing_invoice)
            except Exception as e:
                self.logger.error(f"Error updating draft sales invoice ID {invoice_id}: {e}", exc_info=True)
                return Result.failure([f"An unexpected error occurred while updating sales invoice: {str(e)}"])

    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[SalesInvoice]:
        try:
            return await self.sales_invoice_service.get_by_id(invoice_id)
        except Exception as e:
            self.logger.error(f"Error fetching invoice ID {invoice_id} for dialog: {e}", exc_info=True)
            return None

    async def post_invoice(self, invoice_id: int, user_id: int) -> Result[SalesInvoice]:
        async with self.app_core.db_manager.session() as session:
            try:
                invoice_to_post = await session.get(
                    SalesInvoice, invoice_id, 
                    options=[
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.sales_account),
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.tax_code_obj).selectinload(TaxCode.affects_account),
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj).selectinload(TaxCode.affects_account), 
                        selectinload(SalesInvoice.customer).selectinload(Customer.receivables_account)
                    ]
                )
                if not invoice_to_post:
                    return Result.failure([f"Sales Invoice ID {invoice_id} not found."])
                if invoice_to_post.status != InvoiceStatusEnum.DRAFT.value:
                    return Result.failure([f"Only Draft invoices can be posted. Current status: {invoice_to_post.status}."])

                if not invoice_to_post.customer or not invoice_to_post.customer.is_active:
                    return Result.failure(["Customer is inactive or not found."])
                if not invoice_to_post.customer.receivables_account_id or not invoice_to_post.customer.receivables_account:
                    return Result.failure([f"Customer '{invoice_to_post.customer.name}' does not have a receivables account configured or it's invalid."])
                
                ar_account = invoice_to_post.customer.receivables_account
                if not ar_account.is_active:
                     return Result.failure([f"Configured Accounts Receivable account '{ar_account.code}' for customer is inactive."])

                default_sales_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultSalesRevenue", "4100")
                default_gst_output_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultGSTOutput", "SYS-GST-OUTPUT")
                
                je_lines_data: List[JournalEntryLineData] = []
                
                je_lines_data.append(JournalEntryLineData(
                    account_id=ar_account.id,
                    debit_amount=invoice_to_post.total_amount, 
                    credit_amount=Decimal(0),
                    description=f"A/R for Inv {invoice_to_post.invoice_no}",
                    currency_code=invoice_to_post.currency_code, 
                    exchange_rate=invoice_to_post.exchange_rate
                ))

                for line in invoice_to_post.lines:
                    sales_gl_id_for_line: Optional[int] = None
                    if line.product and line.product.sales_account: 
                        if line.product.sales_account.is_active:
                            sales_gl_id_for_line = line.product.sales_account.id
                        else:
                            self.logger.warning(f"Product '{line.product.name}' sales account '{line.product.sales_account.code}' is inactive for Inv {invoice_to_post.invoice_no}. Falling back.")
                    
                    if not sales_gl_id_for_line and default_sales_acc_code:
                        def_sales_acc = await self.account_service.get_by_code(default_sales_acc_code)
                        if not def_sales_acc or not def_sales_acc.is_active:
                            return Result.failure([f"Default Sales Revenue account '{default_sales_acc_code}' is invalid or inactive."])
                        sales_gl_id_for_line = def_sales_acc.id
                    
                    if not sales_gl_id_for_line: 
                        return Result.failure([f"Could not determine Sales Revenue account for line: {line.description}"])

                    je_lines_data.append(JournalEntryLineData(
                        account_id=sales_gl_id_for_line,
                        debit_amount=Decimal(0),
                        credit_amount=line.line_subtotal, 
                        description=f"Sale: {line.description[:100]} (Inv {invoice_to_post.invoice_no})",
                        currency_code=invoice_to_post.currency_code,
                        exchange_rate=invoice_to_post.exchange_rate
                    ))

                    if line.tax_amount and line.tax_amount != Decimal(0) and line.tax_code:
                        gst_gl_id_for_line: Optional[int] = None
                        line_tax_code_obj = line.tax_code_obj 
                        if line_tax_code_obj and line_tax_code_obj.affects_account:
                            if line_tax_code_obj.affects_account.is_active:
                                gst_gl_id_for_line = line_tax_code_obj.affects_account.id
                            else:
                                self.logger.warning(f"Tax code '{line.tax_code}' affects account '{line_tax_code_obj.affects_account.code}' is inactive for Inv {invoice_to_post.invoice_no}. Falling back.")
                        
                        if not gst_gl_id_for_line and default_gst_output_acc_code: 
                            def_gst_output_acc = await self.account_service.get_by_code(default_gst_output_acc_code)
                            if not def_gst_output_acc or not def_gst_output_acc.is_active:
                                return Result.failure([f"Default GST Output account '{default_gst_output_acc_code}' is invalid or inactive."])
                            gst_gl_id_for_line = def_gst_output_acc.id

                        if not gst_gl_id_for_line: 
                            return Result.failure([f"Could not determine GST Output account for tax on line: {line.description}"])

                        je_lines_data.append(JournalEntryLineData(
                            account_id=gst_gl_id_for_line,
                            debit_amount=Decimal(0),
                            credit_amount=line.tax_amount,
                            description=f"GST Output ({line.tax_code}) for Inv {invoice_to_post.invoice_no}",
                            currency_code=invoice_to_post.currency_code,
                            exchange_rate=invoice_to_post.exchange_rate
                        ))
                
                je_dto = JournalEntryData(
                    journal_type=JournalTypeEnum.SALES.value,
                    entry_date=invoice_to_post.invoice_date,
                    description=f"Sales Invoice {invoice_to_post.invoice_no} to {invoice_to_post.customer.name}",
                    source_type="SalesInvoice", source_id=invoice_to_post.id,
                    user_id=user_id, lines=je_lines_data
                )

                create_je_result = await self.app_core.journal_entry_manager.create_journal_entry(je_dto)
                if not create_je_result.is_success or not create_je_result.value:
                    return Result.failure(["Failed to create journal entry for sales invoice."] + create_je_result.errors)
                
                created_je: JournalEntry = create_je_result.value
                post_je_result = await self.app_core.journal_entry_manager.post_journal_entry(created_je.id, user_id)
                if not post_je_result.is_success:
                    self.logger.error(f"Journal entry ID {created_je.id} for Inv {invoice_to_post.invoice_no} created but failed to post: {post_je_result.errors}")
                    return Result.failure([f"Journal entry created (ID: {created_je.id}) but failed to post."] + post_je_result.errors)

                invoice_to_post.status = InvoiceStatusEnum.APPROVED.value 
                invoice_to_post.journal_entry_id = created_je.id
                invoice_to_post.updated_by_user_id = user_id
                
                session.add(invoice_to_post) 
                await session.flush() 
                await session.refresh(invoice_to_post)
                
                self.logger.info(f"Sales Invoice {invoice_to_post.invoice_no} (ID: {invoice_id}) posted successfully. JE ID: {created_je.id}")
                return Result.success(invoice_to_post)

            except Exception as e:
                self.logger.error(f"Error posting Sales Invoice ID {invoice_id}: {e}", exc_info=True)
                return Result.failure([f"An unexpected error occurred while posting the sales invoice: {str(e)}"])

    async def get_invoices_for_listing(self, 
                                      customer_id: Optional[int] = None,
                                      status: Optional[InvoiceStatusEnum] = None, 
                                      start_date: Optional[date] = None, 
                                      end_date: Optional[date] = None,
                                      page: int = 1, 
                                      page_size: int = 50
                                      ) -> Result[List[SalesInvoiceSummaryData]]:
        try:
            summaries = await self.sales_invoice_service.get_all_summary(
                customer_id=customer_id, status=status,
                start_date=start_date, end_date=end_date,
                page=page, page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching sales invoice listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve sales invoice list: {str(e)}"])


```

# app/business_logic/purchase_invoice_manager.py
```py
# app/business_logic/purchase_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date

from sqlalchemy.orm import selectinload # Required for manager updates that use session directly

from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from app.models.business.vendor import Vendor
from app.models.business.product import Product
# from app.models.accounting.tax_code import TaxCode # Not directly used, TaxCalculator handles it

from app.services.business_services import PurchaseInvoiceService, VendorService, ProductService
from app.services.core_services import SequenceService, ConfigurationService
from app.services.tax_service import TaxCodeService
from app.services.account_service import AccountService
from app.utils.result import Result
from app.utils.pydantic_models import (
    PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceSummaryData,
    PurchaseInvoiceLineBaseData, TaxCalculationResultData
)
from app.tax.tax_calculator import TaxCalculator
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum # ProductTypeEnum for product validation

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class PurchaseInvoiceManager:
    def __init__(self,
                 purchase_invoice_service: PurchaseInvoiceService,
                 vendor_service: VendorService,
                 product_service: ProductService,
                 tax_code_service: TaxCodeService,
                 tax_calculator: TaxCalculator,
                 sequence_service: SequenceService,
                 account_service: AccountService,
                 configuration_service: ConfigurationService,
                 app_core: "ApplicationCore"):
        self.purchase_invoice_service = purchase_invoice_service
        self.vendor_service = vendor_service
        self.product_service = product_service
        self.tax_code_service = tax_code_service
        self.tax_calculator = tax_calculator
        self.sequence_service = sequence_service
        self.account_service = account_service
        self.configuration_service = configuration_service
        self.app_core = app_core
        self.logger = app_core.logger
        # self.logger.info("PurchaseInvoiceManager initialized.") # Moved from stub

    async def _validate_and_prepare_pi_data(
        self, 
        dto: Union[PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData],
        is_update: bool = False
    ) -> Result[Dict[str, Any]]:
        errors: List[str] = []
        
        vendor = await self.vendor_service.get_by_id(dto.vendor_id)
        if not vendor:
            errors.append(f"Vendor with ID {dto.vendor_id} not found.")
        elif not vendor.is_active:
            errors.append(f"Vendor '{vendor.name}' (ID: {dto.vendor_id}) is not active.")

        if not dto.currency_code or len(dto.currency_code) != 3:
            errors.append(f"Invalid currency code: '{dto.currency_code}'.")
        else:
           currency_obj = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
           if not currency_obj or not currency_obj.is_active:
               errors.append(f"Currency '{dto.currency_code}' is invalid or not active.")

        if dto.vendor_invoice_no and not is_update: # Check for duplicate on create
            existing_pi = await self.purchase_invoice_service.get_by_vendor_and_vendor_invoice_no(dto.vendor_id, dto.vendor_invoice_no)
            if existing_pi:
                errors.append(f"Duplicate vendor invoice number '{dto.vendor_invoice_no}' already exists for this vendor.")
        elif dto.vendor_invoice_no and is_update and isinstance(dto, PurchaseInvoiceUpdateData): # Check for duplicate on update if changed
            existing_pi_for_update = await self.purchase_invoice_service.get_by_id(dto.id) # get current PI
            if existing_pi_for_update and existing_pi_for_update.vendor_invoice_no != dto.vendor_invoice_no:
                colliding_pi = await self.purchase_invoice_service.get_by_vendor_and_vendor_invoice_no(dto.vendor_id, dto.vendor_invoice_no)
                if colliding_pi and colliding_pi.id != dto.id:
                    errors.append(f"Duplicate vendor invoice number '{dto.vendor_invoice_no}' already exists for this vendor on another record.")


        calculated_lines_for_orm: List[Dict[str, Any]] = []
        invoice_subtotal_calc = Decimal(0)
        invoice_total_tax_calc = Decimal(0)

        if not dto.lines:
            errors.append("Purchase invoice must have at least one line item.")
        
        for i, line_dto in enumerate(dto.lines):
            line_errors_current_line: List[str] = []
            product: Optional[Product] = None
            line_description = line_dto.description
            unit_price = line_dto.unit_price
            line_purchase_account_id: Optional[int] = None 
            line_tax_account_id: Optional[int] = None

            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product:
                    line_errors_current_line.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active:
                    line_errors_current_line.append(f"Product '{product.name}' is not active on line {i+1}.")
                
                if product: 
                    if not line_description: line_description = product.name
                    if (unit_price is None or unit_price == Decimal(0)) and product.purchase_price is not None:
                        unit_price = product.purchase_price
                    line_purchase_account_id = product.purchase_account_id 
            
            if not line_description: 
                line_errors_current_line.append(f"Description is required on line {i+1}.")
            if unit_price is None: 
                line_errors_current_line.append(f"Unit price is required on line {i+1}.")
                unit_price = Decimal(0) 

            try:
                qty = Decimal(str(line_dto.quantity))
                price = Decimal(str(unit_price))
                discount_pct = Decimal(str(line_dto.discount_percent))
                if qty <= 0: line_errors_current_line.append(f"Quantity must be positive on line {i+1}.")
                if price < 0: line_errors_current_line.append(f"Unit price cannot be negative on line {i+1}.")
                if not (0 <= discount_pct <= 100): line_errors_current_line.append(f"Discount percent must be between 0 and 100 on line {i+1}.")
            except InvalidOperation:
                line_errors_current_line.append(f"Invalid numeric value for quantity, price, or discount on line {i+1}.")
                errors.extend(line_errors_current_line); continue

            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            line_tax_amount_calc = Decimal(0)
            if line_dto.tax_code:
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(
                    amount=line_subtotal_before_tax, tax_code_str=line_dto.tax_code,
                    transaction_type="PurchaseInvoiceLine" # Important for TaxCalculator logic if it differs
                )
                line_tax_amount_calc = tax_calc_result.tax_amount
                line_tax_account_id = tax_calc_result.tax_account_id
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0):
                    tc_check = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check or not tc_check.is_active:
                        line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            
            invoice_subtotal_calc += line_subtotal_before_tax
            invoice_total_tax_calc += line_tax_amount_calc
            if line_errors_current_line: errors.extend(line_errors_current_line)
            
            calculated_lines_for_orm.append({
                "product_id": line_dto.product_id, "description": line_description,
                "quantity": qty, "unit_price": price, "discount_percent": discount_pct,
                "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_subtotal": line_subtotal_before_tax.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "tax_code": line_dto.tax_code, "tax_amount": line_tax_amount_calc.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_total": (line_subtotal_before_tax + line_tax_amount_calc).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "dimension1_id": line_dto.dimension1_id, "dimension2_id": line_dto.dimension2_id,
                "_line_purchase_account_id": line_purchase_account_id,
                "_line_tax_account_id": line_tax_account_id 
            })

        if errors: return Result.failure(errors)
        invoice_grand_total = invoice_subtotal_calc + invoice_total_tax_calc
        return Result.success({
            "header_dto": dto, "vendor_orm": vendor, "calculated_lines_for_orm": calculated_lines_for_orm,
            "invoice_subtotal": invoice_subtotal_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_total_tax": invoice_total_tax_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_grand_total": invoice_grand_total.quantize(Decimal("0.01"), ROUND_HALF_UP),
        })

    async def create_draft_purchase_invoice(self, dto: PurchaseInvoiceCreateData) -> Result[PurchaseInvoice]:
        preparation_result = await self._validate_and_prepare_pi_data(dto)
        if not preparation_result.is_success:
            return Result.failure(preparation_result.errors)
        
        prepared_data = preparation_result.value; assert prepared_data is not None 
        header_dto = cast(PurchaseInvoiceCreateData, prepared_data["header_dto"])

        try:
            our_internal_ref_no = await self.app_core.db_manager.execute_scalar( 
                 "SELECT core.get_next_sequence_value($1);", "purchase_invoice" # Assuming sequence "purchase_invoice"
            )
            if not our_internal_ref_no or not isinstance(our_internal_ref_no, str):
                 self.logger.error(f"Failed to generate purchase invoice number: {our_internal_ref_no}")
                 return Result.failure(["Failed to generate internal invoice number."])

            invoice_orm = PurchaseInvoice(
                invoice_no=our_internal_ref_no, # Our internal reference
                vendor_invoice_no=header_dto.vendor_invoice_no,
                vendor_id=header_dto.vendor_id,
                invoice_date=header_dto.invoice_date, due_date=header_dto.due_date,
                currency_code=header_dto.currency_code, exchange_rate=header_dto.exchange_rate,
                notes=header_dto.notes,
                subtotal=prepared_data["invoice_subtotal"], tax_amount=prepared_data["invoice_total_tax"],
                total_amount=prepared_data["invoice_grand_total"], amount_paid=Decimal(0), 
                status=InvoiceStatusEnum.DRAFT.value, # Default to Draft
                created_by_user_id=header_dto.user_id, updated_by_user_id=header_dto.user_id
            )
            for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                invoice_orm.lines.append(PurchaseInvoiceLine(line_number=i + 1, **orm_line_data))
            
            saved_invoice = await self.purchase_invoice_service.save(invoice_orm)
            self.logger.info(f"Draft Purchase Invoice '{saved_invoice.invoice_no}' created successfully for vendor ID {saved_invoice.vendor_id}.")
            return Result.success(saved_invoice)
        except Exception as e:
            self.logger.error(f"Error creating draft purchase invoice: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred creating purchase invoice: {str(e)}"])

    async def update_draft_purchase_invoice(self, invoice_id: int, dto: PurchaseInvoiceUpdateData) -> Result[PurchaseInvoice]:
        async with self.app_core.db_manager.session() as session: 
            existing_invoice = await session.get(PurchaseInvoice, invoice_id, options=[selectinload(PurchaseInvoice.lines)])
            if not existing_invoice: return Result.failure([f"Purchase Invoice ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only draft purchase invoices can be updated. Current status: {existing_invoice.status}"])

            preparation_result = await self._validate_and_prepare_pi_data(dto, is_update=True)
            if not preparation_result.is_success: return Result.failure(preparation_result.errors)

            prepared_data = preparation_result.value; assert prepared_data is not None 
            header_dto = cast(PurchaseInvoiceUpdateData, prepared_data["header_dto"])

            try:
                # Update header
                existing_invoice.vendor_id = header_dto.vendor_id
                existing_invoice.vendor_invoice_no = header_dto.vendor_invoice_no
                existing_invoice.invoice_date = header_dto.invoice_date
                existing_invoice.due_date = header_dto.due_date
                existing_invoice.currency_code = header_dto.currency_code
                existing_invoice.exchange_rate = header_dto.exchange_rate
                existing_invoice.notes = header_dto.notes
                existing_invoice.subtotal = prepared_data["invoice_subtotal"]
                existing_invoice.tax_amount = prepared_data["invoice_total_tax"]
                existing_invoice.total_amount = prepared_data["invoice_grand_total"]
                existing_invoice.updated_by_user_id = header_dto.user_id
                
                # Replace lines
                for line_orm_to_delete in list(existing_invoice.lines): await session.delete(line_orm_to_delete)
                await session.flush() 

                new_lines_orm: List[PurchaseInvoiceLine] = []
                for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                    orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                    new_lines_orm.append(PurchaseInvoiceLine(line_number=i + 1, **orm_line_data))
                existing_invoice.lines = new_lines_orm 
                
                await session.flush()
                await session.refresh(existing_invoice, attribute_names=['lines']) # Refresh with lines
                self.logger.info(f"Draft Purchase Invoice '{existing_invoice.invoice_no}' (ID: {invoice_id}) updated successfully.")
                return Result.success(existing_invoice)
            except Exception as e:
                self.logger.error(f"Error updating draft purchase invoice ID {invoice_id}: {e}", exc_info=True)
                return Result.failure([f"An unexpected error occurred updating purchase invoice: {str(e)}"])

    async def post_purchase_invoice(self, invoice_id: int, user_id: int) -> Result[PurchaseInvoice]:
        self.logger.info(f"Stub: post_purchase_invoice for ID {invoice_id}")
        # 1. Fetch PI, validate it's Draft.
        # 2. Validations: Vendor active, AP account active, product purchase/inventory accounts active, tax input account active.
        # 3. Construct JournalEntryData:
        #    - Debit Expense/Asset (for each line.line_subtotal, using product.purchase_account_id or default)
        #    - Debit Input GST (for each line.tax_amount, using tax_code.affects_account_id or default)
        #    - Credit Accounts Payable (for invoice.total_amount, using vendor.payables_account_id or default)
        # 4. Create and Post JE via JournalEntryManager.
        # 5. Update PI status to Approved, link journal_entry_id.
        # 6. (Future) Update inventory for 'Inventory' type products.
        return Result.failure(["Post purchase invoice not fully implemented."])

    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        try:
            return await self.purchase_invoice_service.get_by_id(invoice_id)
        except Exception as e:
            self.logger.error(f"Error fetching purchase invoice ID {invoice_id} for dialog: {e}", exc_info=True)
            return None

    async def get_invoices_for_listing(self, 
                                     vendor_id: Optional[int] = None,
                                     status: Optional[InvoiceStatusEnum] = None, 
                                     start_date: Optional[date] = None, 
                                     end_date: Optional[date] = None,
                                     page: int = 1, 
                                     page_size: int = 50
                                     ) -> Result[List[PurchaseInvoiceSummaryData]]:
        try:
            summaries = await self.purchase_invoice_service.get_all_summary(
                vendor_id=vendor_id, status=status, start_date=start_date, end_date=end_date,
                page=page, page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching purchase invoice listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve purchase invoice list: {str(e)}"])


```

# app/business_logic/product_manager.py
```py
# app/business_logic/product_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.product import Product
from app.services.business_services import ProductService
from app.services.account_service import AccountService
from app.services.tax_service import TaxCodeService # For validating tax_code
from app.utils.result import Result
from app.utils.pydantic_models import ProductCreateData, ProductUpdateData, ProductSummaryData
from app.common.enums import ProductTypeEnum # For product_type comparison

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class ProductManager:
    def __init__(self, 
                 product_service: ProductService, 
                 account_service: AccountService, 
                 tax_code_service: TaxCodeService,
                 app_core: "ApplicationCore"):
        self.product_service = product_service
        self.account_service = account_service
        self.tax_code_service = tax_code_service
        self.app_core = app_core
        self.logger = app_core.logger 

    async def get_product_for_dialog(self, product_id: int) -> Optional[Product]:
        """ Fetches a full product/service ORM object for dialog population. """
        try:
            return await self.product_service.get_by_id(product_id)
        except Exception as e:
            self.logger.error(f"Error fetching product ID {product_id} for dialog: {e}", exc_info=True)
            return None

    async def get_products_for_listing(self, 
                                       active_only: bool = True,
                                       product_type_filter: Optional[ProductTypeEnum] = None,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[ProductSummaryData]]:
        """ Fetches a list of product/service summaries for table display. """
        try:
            summaries: List[ProductSummaryData] = await self.product_service.get_all_summary(
                active_only=active_only,
                product_type_filter=product_type_filter,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching product listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve product list: {str(e)}"])

    async def _validate_product_data(self, dto: ProductCreateData | ProductUpdateData, existing_product_id: Optional[int] = None) -> List[str]:
        """ Common validation logic for creating and updating products/services. """
        errors: List[str] = []

        # Validate product_code uniqueness
        if dto.product_code:
            existing_by_code = await self.product_service.get_by_code(dto.product_code)
            if existing_by_code and (existing_product_id is None or existing_by_code.id != existing_product_id):
                errors.append(f"Product code '{dto.product_code}' already exists.")
        else:
             errors.append("Product code is required.") # Pydantic should catch this with min_length

        if not dto.name or not dto.name.strip():
            errors.append("Product name is required.") # Pydantic should catch this

        # Validate GL Accounts
        account_ids_to_check = {
            "Sales Account": (dto.sales_account_id, ['Revenue']),
            "Purchase Account": (dto.purchase_account_id, ['Expense', 'Asset']), # COGS or Asset for purchases
        }
        if dto.product_type == ProductTypeEnum.INVENTORY:
            account_ids_to_check["Inventory Account"] = (dto.inventory_account_id, ['Asset'])
        
        for acc_label, (acc_id, valid_types) in account_ids_to_check.items():
            if acc_id is not None:
                acc = await self.account_service.get_by_id(acc_id)
                if not acc:
                    errors.append(f"{acc_label} ID '{acc_id}' not found.")
                elif not acc.is_active:
                    errors.append(f"{acc_label} '{acc.code} - {acc.name}' is not active.")
                elif acc.account_type not in valid_types:
                    errors.append(f"{acc_label} '{acc.code} - {acc.name}' is not a valid type (Expected: {', '.join(valid_types)}).")

        # Validate Tax Code (string code)
        if dto.tax_code is not None:
            tax_code_obj = await self.tax_code_service.get_tax_code(dto.tax_code)
            if not tax_code_obj:
                errors.append(f"Tax code '{dto.tax_code}' not found.")
            elif not tax_code_obj.is_active:
                errors.append(f"Tax code '{dto.tax_code}' is not active.")

        # Pydantic DTO root_validator already checks inventory_account_id and stock levels based on product_type
        return errors

    async def create_product(self, dto: ProductCreateData) -> Result[Product]:
        validation_errors = await self._validate_product_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            product_orm = Product(
                product_code=dto.product_code, name=dto.name, description=dto.description,
                product_type=dto.product_type.value, # Store enum value
                category=dto.category, unit_of_measure=dto.unit_of_measure, barcode=dto.barcode,
                sales_price=dto.sales_price, purchase_price=dto.purchase_price,
                sales_account_id=dto.sales_account_id, purchase_account_id=dto.purchase_account_id,
                inventory_account_id=dto.inventory_account_id,
                tax_code=dto.tax_code, is_active=dto.is_active,
                min_stock_level=dto.min_stock_level, reorder_point=dto.reorder_point,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_product = await self.product_service.save(product_orm)
            return Result.success(saved_product)
        except Exception as e:
            self.logger.error(f"Error creating product '{dto.product_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the product/service: {str(e)}"])

    async def update_product(self, product_id: int, dto: ProductUpdateData) -> Result[Product]:
        existing_product = await self.product_service.get_by_id(product_id)
        if not existing_product:
            return Result.failure([f"Product/Service with ID {product_id} not found."])

        validation_errors = await self._validate_product_data(dto, existing_product_id=product_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            # Use model_dump to get only provided fields for update
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_product, key):
                    if key == "product_type" and isinstance(value, ProductTypeEnum): # Handle enum
                        setattr(existing_product, key, value.value)
                    else:
                        setattr(existing_product, key, value)
            
            existing_product.updated_by_user_id = dto.user_id
            
            updated_product = await self.product_service.save(existing_product)
            return Result.success(updated_product)
        except Exception as e:
            self.logger.error(f"Error updating product ID {product_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the product/service: {str(e)}"])

    async def toggle_product_active_status(self, product_id: int, user_id: int) -> Result[Product]:
        product = await self.product_service.get_by_id(product_id)
        if not product:
            return Result.failure([f"Product/Service with ID {product_id} not found."])
        
        # Future validation: check if product is used in open sales/purchase orders, or has stock.
        # For now, simple toggle.
        
        product_name_for_log = product.name # Capture before potential changes for logging
        
        product.is_active = not product.is_active
        product.updated_by_user_id = user_id

        try:
            updated_product = await self.product_service.save(product)
            action = "activated" if updated_product.is_active else "deactivated"
            self.logger.info(f"Product/Service '{product_name_for_log}' (ID: {product_id}) {action} by user ID {user_id}.")
            return Result.success(updated_product)
        except Exception as e:
            self.logger.error(f"Error toggling active status for product ID {product_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for product/service: {str(e)}"])


```

# app/business_logic/customer_manager.py
```py
# app/business_logic/customer_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.customer import Customer
from app.services.business_services import CustomerService
from app.services.account_service import AccountService # Corrected import
from app.services.accounting_services import CurrencyService # Correct import
from app.utils.result import Result
from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData, CustomerSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerManager:
    def __init__(self, 
                 customer_service: CustomerService, 
                 account_service: AccountService, 
                 currency_service: CurrencyService, 
                 app_core: "ApplicationCore"):
        self.customer_service = customer_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_customer_for_dialog(self, customer_id: int) -> Optional[Customer]:
        """ Fetches a full customer ORM object for dialog population. """
        try:
            return await self.customer_service.get_by_id(customer_id)
        except Exception as e:
            self.logger.error(f"Error fetching customer ID {customer_id} for dialog: {e}", exc_info=True)
            return None

    async def get_customers_for_listing(self, 
                                       active_only: bool = True,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[CustomerSummaryData]]:
        """ Fetches a list of customer summaries for table display. """
        try:
            # Pydantic DTOs are now directly returned by the service
            summaries: List[CustomerSummaryData] = await self.customer_service.get_all_summary(
                active_only=active_only,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching customer listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve customer list: {str(e)}"])

    async def _validate_customer_data(self, dto: CustomerCreateData | CustomerUpdateData, existing_customer_id: Optional[int] = None) -> List[str]:
        errors: List[str] = []

        if dto.customer_code:
            existing_by_code = await self.customer_service.get_by_code(dto.customer_code)
            if existing_by_code and (existing_customer_id is None or existing_by_code.id != existing_customer_id):
                errors.append(f"Customer code '{dto.customer_code}' already exists.")
        else: # Should be caught by Pydantic if min_length=1
            errors.append("Customer code is required.") 
            
        if dto.name is None or not dto.name.strip(): # Should be caught by Pydantic if min_length=1
            errors.append("Customer name is required.")

        if dto.receivables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.receivables_account_id)
            if not acc:
                errors.append(f"Receivables account ID '{dto.receivables_account_id}' not found.")
            elif acc.account_type != 'Asset': 
                errors.append(f"Account '{acc.code} - {acc.name}' is not an Asset account and cannot be used as receivables account.")
            elif not acc.is_active:
                 errors.append(f"Receivables account '{acc.code} - {acc.name}' is not active.")
            # Ideally, also check if it's specifically marked as an Accounts Receivable control account via a flag or sub_type

        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) 
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        else: # Should be caught by Pydantic if required
             errors.append("Currency code is required.")


        # Pydantic DTO's own root_validator handles gst_no if gst_registered
        # No need to repeat here unless more complex cross-field logic is added.
        return errors

    async def create_customer(self, dto: CustomerCreateData) -> Result[Customer]:
        validation_errors = await self._validate_customer_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            customer_orm = Customer(
                customer_code=dto.customer_code, name=dto.name, legal_name=dto.legal_name,
                uen_no=dto.uen_no, gst_registered=dto.gst_registered, gst_no=dto.gst_no,
                contact_person=dto.contact_person, email=str(dto.email) if dto.email else None, phone=dto.phone,
                address_line1=dto.address_line1, address_line2=dto.address_line2,
                postal_code=dto.postal_code, city=dto.city, country=dto.country,
                credit_terms=dto.credit_terms, credit_limit=dto.credit_limit,
                currency_code=dto.currency_code, is_active=dto.is_active,
                customer_since=dto.customer_since, notes=dto.notes,
                receivables_account_id=dto.receivables_account_id,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_customer = await self.customer_service.save(customer_orm)
            return Result.success(saved_customer)
        except Exception as e:
            self.logger.error(f"Error creating customer '{dto.customer_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the customer: {str(e)}"])

    async def update_customer(self, customer_id: int, dto: CustomerUpdateData) -> Result[Customer]:
        existing_customer = await self.customer_service.get_by_id(customer_id)
        if not existing_customer:
            return Result.failure([f"Customer with ID {customer_id} not found."])

        validation_errors = await self._validate_customer_data(dto, existing_customer_id=customer_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            # Update fields from DTO
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_customer, key):
                    # Special handling for EmailStr which might be an object
                    if key == 'email' and value is not None:
                        setattr(existing_customer, key, str(value))
                    else:
                        setattr(existing_customer, key, value)
            
            existing_customer.updated_by_user_id = dto.user_id
            
            updated_customer = await self.customer_service.save(existing_customer)
            return Result.success(updated_customer)
        except Exception as e:
            self.logger.error(f"Error updating customer ID {customer_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the customer: {str(e)}"])

    async def toggle_customer_active_status(self, customer_id: int, user_id: int) -> Result[Customer]:
        customer = await self.customer_service.get_by_id(customer_id)
        if not customer:
            return Result.failure([f"Customer with ID {customer_id} not found."])
        
        customer.is_active = not customer.is_active
        customer.updated_by_user_id = user_id

        try:
            updated_customer = await self.customer_service.save(customer)
            action = "activated" if updated_customer.is_active else "deactivated"
            self.logger.info(f"Customer '{updated_customer.name}' (ID: {customer_id}) {action} by user ID {user_id}.")
            return Result.success(updated_customer)
        except Exception as e:
            self.logger.error(f"Error toggling active status for customer ID {customer_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for customer: {str(e)}"])

```

# app/accounting/__init__.py
```py
# File: app/accounting/__init__.py
# (Content as previously generated, verified)
from .chart_of_accounts_manager import ChartOfAccountsManager
from .journal_entry_manager import JournalEntryManager
from .fiscal_period_manager import FiscalPeriodManager
from .currency_manager import CurrencyManager

__all__ = [
    "ChartOfAccountsManager",
    "JournalEntryManager",
    "FiscalPeriodManager",
    "CurrencyManager",
]

```

# app/accounting/journal_entry_manager.py
```py
# File: app/accounting/journal_entry_manager.py
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta 

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, 
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator,
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        self.sequence_generator = sequence_generator
        self.app_core = app_core

    async def create_journal_entry(self, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # Pydantic model JournalEntryData already validates balanced lines and non-empty lines
        
        fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date)
        if not fiscal_period or fiscal_period.status != 'Open':
            return Result.failure([f"No open fiscal period found for the entry date {entry_data.entry_date} or period is not open."])
        
        # Consider using core.get_next_sequence_value DB function via db_manager.execute_scalar
        # for better atomicity if SequenceGenerator's Python logic is a concern.
        # For now, assuming SequenceGenerator is sufficient for desktop app context.
        entry_no_str = await self.sequence_generator.next_sequence("journal_entry") 
        
        current_user_id = entry_data.user_id

        journal_entry_orm = JournalEntry(
            entry_no=entry_no_str,
            journal_type=entry_data.journal_type,
            entry_date=entry_data.entry_date,
            fiscal_period_id=fiscal_period.id,
            description=entry_data.description,
            reference=entry_data.reference,
            is_recurring=entry_data.is_recurring,
            recurring_pattern_id=entry_data.recurring_pattern_id,
            is_posted=False, # New entries are always drafts
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            created_by_user_id=current_user_id,
            updated_by_user_id=current_user_id
        )
        
        for i, line_dto in enumerate(entry_data.lines, 1):
            account = await self.account_service.get_by_id(line_dto.account_id)
            if not account or not account.is_active:
                return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
            
            # TODO: Add validation for tax_code, currency_code, dimension_ids existence if provided from their respective services.

            line_orm = JournalEntryLine(
                line_number=i,
                account_id=line_dto.account_id,
                description=line_dto.description,
                debit_amount=line_dto.debit_amount,
                credit_amount=line_dto.credit_amount,
                currency_code=line_dto.currency_code,
                exchange_rate=line_dto.exchange_rate,
                tax_code=line_dto.tax_code,
                tax_amount=line_dto.tax_amount,
                dimension1_id=line_dto.dimension1_id,
                dimension2_id=line_dto.dimension2_id
            )
            journal_entry_orm.lines.append(line_orm)
        
        try:
            saved_entry = await self.journal_service.save(journal_entry_orm)
            return Result.success(saved_entry)
        except Exception as e:
            self.app_core.db_manager.logger.error(f"Error saving journal entry: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save journal entry: {str(e)}"])

    async def update_journal_entry(self, entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # Use a single session for atomicity
            existing_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)]) # Eager load lines
            if not existing_entry:
                return Result.failure([f"Journal entry ID {entry_id} not found for update."])
            if existing_entry.is_posted:
                return Result.failure([f"Cannot update a posted journal entry: {existing_entry.entry_no}."])

            fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date) # This might use a different session if not passed
            if not fiscal_period or fiscal_period.status != 'Open': # Re-check fiscal period for new date
                fp_check_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
                fp_res = await session.execute(fp_check_stmt)
                fiscal_period_in_session = fp_res.scalars().first()
                if not fiscal_period_in_session:
                     return Result.failure([f"No open fiscal period found for the new entry date {entry_data.entry_date} or period is not open."])
                fiscal_period_id = fiscal_period_in_session.id
            else:
                fiscal_period_id = fiscal_period.id


            current_user_id = entry_data.user_id

            # Update header fields
            existing_entry.journal_type = entry_data.journal_type
            existing_entry.entry_date = entry_data.entry_date
            existing_entry.fiscal_period_id = fiscal_period_id
            existing_entry.description = entry_data.description
            existing_entry.reference = entry_data.reference
            existing_entry.is_recurring = entry_data.is_recurring
            existing_entry.recurring_pattern_id = entry_data.recurring_pattern_id
            existing_entry.source_type = entry_data.source_type
            existing_entry.source_id = entry_data.source_id
            existing_entry.updated_by_user_id = current_user_id
            
            # Line Handling: Clear existing lines and add new ones
            # SQLAlchemy's cascade="all, delete-orphan" will handle DB deletions on flush/commit
            # if the lines are removed from the collection.
            for line in list(existing_entry.lines): # Iterate over a copy for safe removal
                session.delete(line) # Explicitly delete old lines from session
            existing_entry.lines.clear() # Clear the collection itself
            
            await session.flush() # Flush deletions of old lines

            new_lines_orm: List[JournalEntryLine] = []
            for i, line_dto in enumerate(entry_data.lines, 1):
                # Account validation (ensure account_service uses the same session or is session-agnostic for reads)
                # For simplicity, assume account_service can be called outside this transaction for validation reads.
                account = await self.account_service.get_by_id(line_dto.account_id) 
                if not account or not account.is_active:
                    # This will cause the outer session to rollback due to exception
                    raise ValueError(f"Invalid or inactive account ID {line_dto.account_id} on line {i} during update.")
                
                new_lines_orm.append(JournalEntryLine(
                    # journal_entry_id is set by relationship backref
                    line_number=i,
                    account_id=line_dto.account_id,
                    description=line_dto.description,
                    debit_amount=line_dto.debit_amount,
                    credit_amount=line_dto.credit_amount,
                    currency_code=line_dto.currency_code,
                    exchange_rate=line_dto.exchange_rate,
                    tax_code=line_dto.tax_code,
                    tax_amount=line_dto.tax_amount,
                    dimension1_id=line_dto.dimension1_id,
                    dimension2_id=line_dto.dimension2_id
                ))
            existing_entry.lines.extend(new_lines_orm)
            session.add(existing_entry) # Re-add to session if it became detached, or ensure it's managed
            
            try:
                await session.commit() # Commit changes for header and new lines
                await session.refresh(existing_entry) # Refresh to get any DB-generated values or ensure state
                if existing_entry.lines: await session.refresh(existing_entry, attribute_names=['lines'])
                return Result.success(existing_entry)
            except Exception as e:
                # Session context manager handles rollback
                self.app_core.db_manager.logger.error(f"Error updating journal entry ID {entry_id}: {e}", exc_info=True) # type: ignore
                return Result.failure([f"Failed to update journal entry: {str(e)}"])


    async def post_journal_entry(self, entry_id: int, user_id: int) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            entry = await session.get(JournalEntry, entry_id) # Fetch within current session
            if not entry:
                return Result.failure([f"Journal entry ID {entry_id} not found."])
            
            if entry.is_posted:
                return Result.failure([f"Journal entry '{entry.entry_no}' is already posted."])
            
            # Fetch fiscal period within the same session
            fiscal_period = await session.get(FiscalPeriod, entry.fiscal_period_id)
            if not fiscal_period or fiscal_period.status != 'Open': 
                return Result.failure([f"Cannot post. Fiscal period for entry date is not open. Current status: {fiscal_period.status if fiscal_period else 'Unknown'}."])
            
            entry.is_posted = True
            entry.updated_by_user_id = user_id
            session.add(entry)
            
            try:
                await session.commit()
                await session.refresh(entry)
                return Result.success(entry)
            except Exception as e:
                self.app_core.db_manager.logger.error(f"Error posting journal entry ID {entry_id}: {e}", exc_info=True) # type: ignore
                return Result.failure([f"Failed to post journal entry: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        # This method performs multiple DB operations and should be transactional.
        async with self.app_core.db_manager.session() as session: # type: ignore
            original_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)]) # Fetch within session
            if not original_entry:
                return Result.failure([f"Journal entry ID {entry_id} not found for reversal."])
            if not original_entry.is_posted:
                return Result.failure(["Only posted entries can be reversed."])
            if original_entry.is_reversed or original_entry.reversing_entry_id is not None:
                return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed."])

            # Fetch reversal fiscal period within the same session
            reversal_fp_stmt = select(FiscalPeriod).where(
                FiscalPeriod.start_date <= reversal_date, 
                FiscalPeriod.end_date >= reversal_date, 
                FiscalPeriod.status == 'Open'
            )
            reversal_fp_res = await session.execute(reversal_fp_stmt)
            reversal_fiscal_period = reversal_fp_res.scalars().first()

            if not reversal_fiscal_period:
                return Result.failure([f"No open fiscal period found for reversal date {reversal_date} or period is not open."])

            # Call DB function for sequence if preferred, or Python SequenceGenerator
            # Assuming Python SequenceGenerator for now
            reversal_entry_no = await self.sequence_generator.next_sequence("journal_entry", prefix="RJE-")
            
            reversal_lines_orm: List[JournalEntryLine] = []
            for orig_line in original_entry.lines:
                reversal_lines_orm.append(JournalEntryLine(
                    account_id=orig_line.account_id, description=f"Reversal: {orig_line.description or ''}",
                    debit_amount=orig_line.credit_amount, credit_amount=orig_line.debit_amount, 
                    currency_code=orig_line.currency_code, exchange_rate=orig_line.exchange_rate,
                    tax_code=orig_line.tax_code, 
                    tax_amount=-orig_line.tax_amount if orig_line.tax_amount is not None else Decimal(0), 
                    dimension1_id=orig_line.dimension1_id, dimension2_id=orig_line.dimension2_id
                ))
            
            reversal_je_orm = JournalEntry(
                entry_no=reversal_entry_no, journal_type=original_entry.journal_type,
                entry_date=reversal_date, fiscal_period_id=reversal_fiscal_period.id,
                description=description or f"Reversal of entry {original_entry.entry_no}",
                reference=f"REV:{original_entry.entry_no}",
                is_posted=False, # Reversal is initially a draft, can be auto-posted if needed
                source_type="JournalEntryReversalSource", source_id=original_entry.id,
                created_by_user_id=user_id, updated_by_user_id=user_id,
                lines=reversal_lines_orm # Associate lines directly
            )
            session.add(reversal_je_orm)
            
            original_entry.is_reversed = True
            # We need the ID of reversal_je_orm, so flush to get it.
            await session.flush() # This will assign ID to reversal_je_orm
            original_entry.reversing_entry_id = reversal_je_orm.id
            original_entry.updated_by_user_id = user_id
            session.add(original_entry) # Add original_entry back to session if it wasn't already managed or to mark it dirty
            
            try:
                await session.commit()
                await session.refresh(reversal_je_orm) # Refresh to get all attributes after commit
                if reversal_je_orm.lines: await session.refresh(reversal_je_orm, attribute_names=['lines'])
                return Result.success(reversal_je_orm)
            except Exception as e:
                # Session context manager handles rollback
                self.app_core.db_manager.logger.error(f"Error reversing journal entry ID {entry_id}: {e}", exc_info=True) # type: ignore
                return Result.failure([f"Failed to reverse journal entry: {str(e)}"])


    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        # (Logic from previous version is mostly fine, minor refinement if needed)
        next_date = last_date
        # ... (same logic as before, ensure relativedelta is imported and used)
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month)
                except ValueError: next_date = next_date + relativedelta(day=31) 
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month: 
                 try: next_date = next_date.replace(day=day_of_month, month=last_date.month)
                 except ValueError: next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)
        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            # Specific day_of_week logic with relativedelta can be complex, e.g. relativedelta(weekday=MO(+1))
            # For now, simple interval is used.
        elif frequency == 'Daily':
            next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                 try: next_date = next_date.replace(day=day_of_month)
                 except ValueError: next_date = next_date + relativedelta(day=31)
        else:
            raise NotImplementedError(f"Frequency '{frequency}' not supported for next date calculation.")
        return next_date


    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date)
        generated_results: List[Result[JournalEntry]] = []

        for pattern in patterns_due:
            if not pattern.template_journal_entry: # Due to joinedload, this should be populated
                self.app_core.db_manager.logger.error(f"Template JE not loaded for pattern ID {pattern.id}. Skipping.") # type: ignore
                generated_results.append(Result.failure([f"Template JE not loaded for pattern '{pattern.name}'."]))
                continue
            
            # Ensure next_generation_date is valid
            entry_date_for_new_je = pattern.next_generation_date
            if not entry_date_for_new_je : continue # Should have been filtered by service

            template_entry = pattern.template_journal_entry
            
            new_je_lines_data = [
                JournalEntryLineData(
                    account_id=line.account_id, description=line.description,
                    debit_amount=line.debit_amount, credit_amount=line.credit_amount,
                    currency_code=line.currency_code, exchange_rate=line.exchange_rate,
                    tax_code=line.tax_code, tax_amount=line.tax_amount,
                    dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id
                ) for line in template_entry.lines
            ]
            
            new_je_data = JournalEntryData(
                journal_type=template_entry.journal_type, entry_date=entry_date_for_new_je,
                description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})",
                reference=template_entry.reference, user_id=user_id, lines=new_je_lines_data,
                recurring_pattern_id=pattern.id, source_type="RecurringPattern", source_id=pattern.id
            )
            
            create_result = await self.create_journal_entry(new_je_data)
            generated_results.append(create_result)
            
            if create_result.is_success:
                async with self.app_core.db_manager.session() as session: # type: ignore
                    # Re-fetch pattern in this session to update it
                    pattern_to_update = await session.get(RecurringPattern, pattern.id)
                    if pattern_to_update:
                        pattern_to_update.last_generated_date = entry_date_for_new_je
                        try:
                            next_gen = self._calculate_next_generation_date(
                                pattern_to_update.last_generated_date, pattern_to_update.frequency, 
                                pattern_to_update.interval_value, pattern_to_update.day_of_month, 
                                pattern_to_update.day_of_week
                            )
                            if pattern_to_update.end_date and next_gen > pattern_to_update.end_date:
                                pattern_to_update.next_generation_date = None 
                                pattern_to_update.is_active = False 
                            else:
                                pattern_to_update.next_generation_date = next_gen
                        except NotImplementedError:
                            pattern_to_update.next_generation_date = None
                            pattern_to_update.is_active = False 
                            self.app_core.db_manager.logger.warning(f"Next gen date calc not implemented for pattern {pattern_to_update.name}, deactivating.") # type: ignore
                        
                        pattern_to_update.updated_by_user_id = user_id 
                        session.add(pattern_to_update)
                        await session.commit()
                    else:
                        self.app_core.db_manager.logger.error(f"Failed to re-fetch pattern ID {pattern.id} for update after recurring JE generation.") # type: ignore
        return generated_results

    async def get_journal_entry_for_dialog(self, entry_id: int) -> Optional[JournalEntry]:
        return await self.journal_service.get_by_id(entry_id)

    async def get_journal_entries_for_listing(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]:
        filters = filters or {}
        try:
            summary_data = await self.journal_service.get_all_summary(
                start_date_filter=filters.get("start_date"),
                end_date_filter=filters.get("end_date"),
                status_filter=filters.get("status"),
                entry_no_filter=filters.get("entry_no"),
                description_filter=filters.get("description")
            )
            return Result.success(summary_data)
        except Exception as e:
            self.app_core.db_manager.logger.error(f"Error fetching JE summaries for listing: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to retrieve journal entry summaries: {str(e)}"])

```

# app/accounting/currency_manager.py
```py
# File: app/accounting/currency_manager.py
# (Content as previously generated, verified - needs TYPE_CHECKING for ApplicationCore)
# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.accounting_services import CurrencyService, ExchangeRateService 
from typing import Optional, List, Any, TYPE_CHECKING
from datetime import date
from decimal import Decimal
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class CurrencyManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        # Assuming these service properties exist on app_core and are correctly typed there
        self.currency_service: CurrencyService = app_core.currency_repo_service # type: ignore 
        self.exchange_rate_service: ExchangeRateService = app_core.exchange_rate_service # type: ignore
    
    async def get_active_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all_active()

    async def get_exchange_rate(self, from_currency_code: str, to_currency_code: str, rate_date: date) -> Optional[Decimal]:
        rate_obj = await self.exchange_rate_service.get_rate_for_date(from_currency_code, to_currency_code, rate_date)
        return rate_obj.exchange_rate_value if rate_obj else None

    async def update_exchange_rate(self, from_code:str, to_code:str, r_date:date, rate:Decimal, user_id:int) -> Result[ExchangeRate]:
        existing_rate = await self.exchange_rate_service.get_rate_for_date(from_code, to_code, r_date)
        orm_object: ExchangeRate
        if existing_rate:
            existing_rate.exchange_rate_value = rate
            existing_rate.updated_by_user_id = user_id
            orm_object = existing_rate
        else:
            orm_object = ExchangeRate(
                from_currency_code=from_code, to_currency_code=to_code, rate_date=r_date,
                exchange_rate_value=rate, 
                created_by_user_id=user_id, updated_by_user_id=user_id 
            )
        
        saved_obj = await self.exchange_rate_service.save(orm_object)
        return Result.success(saved_obj)

    async def get_all_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all()

    async def get_currency_by_code(self, code: str) -> Optional[Currency]:
        return await self.currency_service.get_by_id(code)

```

# app/accounting/chart_of_accounts_manager.py
```py
# File: app/accounting/chart_of_accounts_manager.py
# (Content previously updated to use AccountCreateData/UpdateData, ensure consistency)
# Key: Uses AccountService. User ID comes from DTO which inherits UserAuditData.
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from app.models.accounting.account import Account 
from app.services.account_service import AccountService 
from app.utils.result import Result
from app.utils.pydantic_models import AccountCreateData, AccountUpdateData, AccountValidator
# from app.core.application_core import ApplicationCore # Removed direct import
from decimal import Decimal
from datetime import date # Added for type hint in deactivate_account

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class ChartOfAccountsManager:
    def __init__(self, account_service: AccountService, app_core: "ApplicationCore"):
        self.account_service = account_service
        self.account_validator = AccountValidator() 
        self.app_core = app_core 

    async def create_account(self, account_data: AccountCreateData) -> Result[Account]:
        validation_result = self.account_validator.validate_create(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        existing = await self.account_service.get_by_code(account_data.code)
        if existing:
            return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        account = Account(
            code=account_data.code, name=account_data.name,
            account_type=account_data.account_type, sub_type=account_data.sub_type,
            tax_treatment=account_data.tax_treatment, gst_applicable=account_data.gst_applicable,
            description=account_data.description, parent_id=account_data.parent_id,
            report_group=account_data.report_group, is_control_account=account_data.is_control_account,
            is_bank_account=account_data.is_bank_account, opening_balance=account_data.opening_balance,
            opening_balance_date=account_data.opening_balance_date, is_active=account_data.is_active,
            created_by_user_id=current_user_id, 
            updated_by_user_id=current_user_id 
        )
        
        try:
            saved_account = await self.account_service.save(account)
            return Result.success(saved_account)
        except Exception as e:
            return Result.failure([f"Failed to save account: {str(e)}"])
    
    async def update_account(self, account_data: AccountUpdateData) -> Result[Account]:
        existing_account = await self.account_service.get_by_id(account_data.id)
        if not existing_account:
            return Result.failure([f"Account with ID {account_data.id} not found."])
        
        validation_result = self.account_validator.validate_update(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        if account_data.code != existing_account.code:
            code_exists = await self.account_service.get_by_code(account_data.code)
            if code_exists and code_exists.id != existing_account.id:
                return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        existing_account.code = account_data.code; existing_account.name = account_data.name
        existing_account.account_type = account_data.account_type; existing_account.sub_type = account_data.sub_type
        existing_account.tax_treatment = account_data.tax_treatment; existing_account.gst_applicable = account_data.gst_applicable
        existing_account.description = account_data.description; existing_account.parent_id = account_data.parent_id
        existing_account.report_group = account_data.report_group; existing_account.is_control_account = account_data.is_control_account
        existing_account.is_bank_account = account_data.is_bank_account; existing_account.opening_balance = account_data.opening_balance
        existing_account.opening_balance_date = account_data.opening_balance_date; existing_account.is_active = account_data.is_active
        existing_account.updated_by_user_id = current_user_id
        
        try:
            updated_account = await self.account_service.save(existing_account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to update account: {str(e)}"])
            
    async def deactivate_account(self, account_id: int, user_id: int) -> Result[Account]:
        account = await self.account_service.get_by_id(account_id)
        if not account:
            return Result.failure([f"Account with ID {account_id} not found."])
        
        if not account.is_active:
             return Result.failure([f"Account '{account.code}' is already inactive."])

        if not hasattr(self.app_core, 'journal_service'): 
            return Result.failure(["Journal service not available for balance check."])

        total_current_balance = await self.app_core.journal_service.get_account_balance(account_id, date.today()) 

        if total_current_balance != Decimal(0):
            return Result.failure([f"Cannot deactivate account '{account.code}' as it has a non-zero balance ({total_current_balance:.2f})."])

        account.is_active = False
        account.updated_by_user_id = user_id 
        
        try:
            updated_account = await self.account_service.save(account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to deactivate account: {str(e)}"])

    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        try:
            tree = await self.account_service.get_account_tree(active_only=active_only)
            return tree 
        except Exception as e:
            print(f"Error getting account tree: {e}") 
            return []

    async def get_accounts_for_selection(self, account_type: Optional[str] = None, active_only: bool = True) -> List[Account]:
        if account_type:
            return await self.account_service.get_by_type(account_type, active_only=active_only)
        elif active_only:
            return await self.account_service.get_all_active()
        else:
            # Assuming get_all() exists on account_service, if not, this path needs adjustment
            if hasattr(self.account_service, 'get_all'):
                 return await self.account_service.get_all()
            else: # Fallback to active if get_all not present for some reason
                 return await self.account_service.get_all_active()

```

# app/accounting/fiscal_period_manager.py
```py
# File: app/accounting/fiscal_period_manager.py
from typing import List, Optional, TYPE_CHECKING # Removed Any, will use specific type
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select # Added for explicit select usage

from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result
from app.utils.pydantic_models import FiscalYearCreateData 
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from sqlalchemy.ext.asyncio import AsyncSession # For session type hint

class FiscalPeriodManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service 
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service 
        
    async def create_fiscal_year_and_periods(self, fy_data: FiscalYearCreateData) -> Result[FiscalYear]:
        if fy_data.start_date >= fy_data.end_date:
            return Result.failure(["Fiscal year start date must be before end date."])

        existing_by_name = await self.fiscal_year_service.get_by_name(fy_data.year_name)
        if existing_by_name:
            return Result.failure([f"A fiscal year with the name '{fy_data.year_name}' already exists."])

        overlapping_fy = await self.fiscal_year_service.get_by_date_overlap(fy_data.start_date, fy_data.end_date)
        if overlapping_fy:
            return Result.failure([f"The proposed date range overlaps with existing fiscal year '{overlapping_fy.year_name}' ({overlapping_fy.start_date} - {overlapping_fy.end_date})."])

        async with self.app_core.db_manager.session() as session: # type: ignore # session is AsyncSession here
            fy = FiscalYear(
                year_name=fy_data.year_name, 
                start_date=fy_data.start_date, 
                end_date=fy_data.end_date, 
                created_by_user_id=fy_data.user_id, 
                updated_by_user_id=fy_data.user_id,
                is_closed=False 
            )
            session.add(fy)
            await session.flush() 
            await session.refresh(fy) 

            if fy_data.auto_generate_periods and fy_data.auto_generate_periods in ["Month", "Quarter"]:
                # Pass the existing session to the internal method
                period_generation_result = await self._generate_periods_for_year_internal(
                    fy, fy_data.auto_generate_periods, fy_data.user_id, session # Pass session
                )
                if not period_generation_result.is_success:
                    # No need to explicitly rollback here, 'async with session' handles it on exception.
                    # If period_generation_result itself raises an exception that's caught outside,
                    # the session context manager will rollback.
                    # If it returns a failure Result, we need to raise an exception to trigger rollback
                    # or handle it such that the fiscal year is not considered fully created.
                    # For now, let's assume if period generation fails, we raise to rollback.
                    # This means _generate_periods_for_year_internal should raise on critical failure.
                    # Or, the manager can decide to keep the FY and return warnings.
                    # Let's make it so that failure to generate periods makes the whole operation fail.
                    raise Exception(f"Failed to generate periods for '{fy.year_name}': {', '.join(period_generation_result.errors)}")
            
            # If we reach here, commit will happen automatically when 'async with session' exits.
            return Result.success(fy)
        
        # This return Result.failure is less likely to be hit due to `async with` handling exceptions
        return Result.failure(["An unexpected error occurred outside the transaction for fiscal year creation."])


    async def _generate_periods_for_year_internal(self, fiscal_year: FiscalYear, period_type: str, user_id: int, session: "AsyncSession") -> Result[List[FiscalPeriod]]:
        if not fiscal_year or not fiscal_year.id:
            # This should raise an exception to trigger rollback in the calling method
            raise ValueError("Valid FiscalYear object with an ID must be provided for period generation.")
        
        stmt_existing = select(FiscalPeriod).where(
            FiscalPeriod.fiscal_year_id == fiscal_year.id,
            FiscalPeriod.period_type == period_type
        )
        existing_periods_result = await session.execute(stmt_existing)
        if existing_periods_result.scalars().first():
             raise ValueError(f"{period_type} periods already exist for fiscal year '{fiscal_year.year_name}'.")


        periods: List[FiscalPeriod] = []
        current_start_date = fiscal_year.start_date
        fy_end_date = fiscal_year.end_date
        period_number = 1

        while current_start_date <= fy_end_date:
            current_end_date: date
            period_name: str

            if period_type == "Month":
                current_end_date = current_start_date + relativedelta(months=1) - relativedelta(days=1)
                if current_end_date > fy_end_date: current_end_date = fy_end_date
                period_name = f"{current_start_date.strftime('%B %Y')}"
            
            elif period_type == "Quarter":
                month_end_of_third_month = current_start_date + relativedelta(months=2, day=1) + relativedelta(months=1) - relativedelta(days=1)
                current_end_date = month_end_of_third_month
                if current_end_date > fy_end_date: current_end_date = fy_end_date
                period_name = f"Q{period_number} {fiscal_year.year_name}"
            else: 
                raise ValueError(f"Invalid period type '{period_type}' during generation.")

            fp = FiscalPeriod(
                fiscal_year_id=fiscal_year.id, name=period_name,
                start_date=current_start_date, end_date=current_end_date,
                period_type=period_type, status="Open", period_number=period_number,
                is_adjustment=False,
                created_by_user_id=user_id, updated_by_user_id=user_id
            )
            session.add(fp) 
            periods.append(fp)

            if current_end_date >= fy_end_date: break 
            current_start_date = current_end_date + relativedelta(days=1)
            period_number += 1
        
        await session.flush() # Flush within the session passed by the caller
        for p in periods: 
            await session.refresh(p)
            
        return Result.success(periods)

    async def close_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Closed': return Result.failure(["Period is already closed."])
        if period.status == 'Archived': return Result.failure(["Cannot close an archived period."])
        
        period.status = 'Closed'
        period.updated_by_user_id = user_id
        # The service's update method will handle the commit with its own session
        updated_period = await self.fiscal_period_service.update(period) 
        return Result.success(updated_period)

    async def reopen_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Open': return Result.failure(["Period is already open."])
        if period.status == 'Archived': return Result.failure(["Cannot reopen an archived period."])
        
        fiscal_year = await self.fiscal_year_service.get_by_id(period.fiscal_year_id)
        if fiscal_year and fiscal_year.is_closed:
            return Result.failure(["Cannot reopen period as its fiscal year is closed."])

        period.status = 'Open'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def get_current_fiscal_period(self, target_date: Optional[date] = None) -> Optional[FiscalPeriod]:
        if target_date is None:
            target_date = date.today()
        return await self.fiscal_period_service.get_by_date(target_date)

    async def get_all_fiscal_years(self) -> List[FiscalYear]:
        return await self.fiscal_year_service.get_all()

    async def get_fiscal_year_by_id(self, fy_id: int) -> Optional[FiscalYear]:
        return await self.fiscal_year_service.get_by_id(fy_id)

    async def get_periods_for_fiscal_year(self, fiscal_year_id: int) -> List[FiscalPeriod]:
        return await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year_id)

    async def close_fiscal_year(self, fiscal_year_id: int, user_id: int) -> Result[FiscalYear]:
        fy = await self.fiscal_year_service.get_by_id(fiscal_year_id)
        if not fy:
            return Result.failure([f"Fiscal Year ID {fiscal_year_id} not found."])
        if fy.is_closed:
            return Result.failure([f"Fiscal Year '{fy.year_name}' is already closed."])

        periods = await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year_id)
        open_periods = [p for p in periods if p.status == 'Open']
        if open_periods:
            return Result.failure([f"Cannot close fiscal year '{fy.year_name}'. Following periods are still open: {[p.name for p in open_periods]}"])
        
        print(f"Performing year-end closing entries for FY '{fy.year_name}' (conceptual)...")

        fy.is_closed = True
        fy.closed_date = datetime.utcnow() 
        fy.closed_by_user_id = user_id
        fy.updated_by_user_id = user_id 
        
        try:
            updated_fy = await self.fiscal_year_service.save(fy)
            return Result.success(updated_fy)
        except Exception as e:
            return Result.failure([f"Error closing fiscal year: {str(e)}"])

```

# app/common/enums.py
```py
# File: app/common/enums.py
# (Content as previously generated and verified)
from enum import Enum

class AccountCategory(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class AccountTypeEnum(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class JournalTypeEnum(Enum): 
    GENERAL = "General" 
    SALES = "Sales"
    PURCHASE = "Purchase"
    CASH_RECEIPT = "Cash Receipt" 
    CASH_DISBURSEMENT = "Cash Disbursement" 
    PAYROLL = "Payroll"
    OPENING_BALANCE = "Opening Balance"
    ADJUSTMENT = "Adjustment"

class FiscalPeriodTypeEnum(Enum): 
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year" 

class FiscalPeriodStatusEnum(Enum): 
    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

class TaxTypeEnum(Enum): 
    GST = "GST"
    INCOME_TAX = "Income Tax"
    WITHHOLDING_TAX = "Withholding Tax"

class ProductTypeEnum(Enum): 
    INVENTORY = "Inventory"
    SERVICE = "Service"
    NON_INVENTORY = "Non-Inventory"

class GSTReturnStatusEnum(Enum): 
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    AMENDED = "Amended"

class InventoryMovementTypeEnum(Enum): 
    PURCHASE = "Purchase"
    SALE = "Sale"
    ADJUSTMENT = "Adjustment"
    TRANSFER = "Transfer"
    RETURN = "Return"
    OPENING = "Opening"

class InvoiceStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    SENT = "Sent" 
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    VOIDED = "Voided"
    DISPUTED = "Disputed" 

class BankTransactionTypeEnum(Enum): 
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER = "Transfer"
    INTEREST = "Interest"
    FEE = "Fee"
    ADJUSTMENT = "Adjustment"

class PaymentTypeEnum(Enum): 
    CUSTOMER_PAYMENT = "Customer Payment"
    VENDOR_PAYMENT = "Vendor Payment"
    REFUND = "Refund"
    CREDIT_NOTE_APPLICATION = "Credit Note" 
    OTHER = "Other"

class PaymentMethodEnum(Enum): 
    CASH = "Cash"
    CHECK = "Check"
    BANK_TRANSFER = "Bank Transfer"
    CREDIT_CARD = "Credit Card"
    GIRO = "GIRO"
    PAYNOW = "PayNow"
    OTHER = "Other"

class PaymentEntityTypeEnum(Enum): 
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    OTHER = "Other"

class PaymentStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    COMPLETED = "Completed" 
    VOIDED = "Voided"
    RETURNED = "Returned" 

class PaymentAllocationDocTypeEnum(Enum): 
    SALES_INVOICE = "Sales Invoice"
    PURCHASE_INVOICE = "Purchase Invoice"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    OTHER = "Other"

class WHCertificateStatusEnum(Enum): 
    DRAFT = "Draft"
    ISSUED = "Issued"
    VOIDED = "Voided"

class DataChangeTypeEnum(Enum): 
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"

class RecurringFrequencyEnum(Enum): 
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"

```

