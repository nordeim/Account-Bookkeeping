# app/models/business/bank_transaction.py
```py
# File: app/models/business/bank_transaction.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.business.bank_account import BankAccount
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
import datetime
from decimal import Decimal
from typing import Optional

class BankTransaction(Base, TimestampMixin):
    __tablename__ = 'bank_transactions'
    __table_args__ = (
        CheckConstraint("transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')", name='ck_bank_transactions_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=False)
    transaction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    statement_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    statement_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    bank_account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="bank_transactions")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # Simplified
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

```

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
from typing import Dict, Any, Literal, List, Optional, TYPE_CHECKING # Added TYPE_CHECKING
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4 
from reportlab.lib.units import inch, cm 
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
# from app.core.application_core import ApplicationCore # Removed direct import
from decimal import Decimal 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class ReportEngine:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal for ApplicationCore
        self.app_core = app_core

    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes:
        if format_type == "pdf":
            return self._export_to_pdf_generic(report_data)
        elif format_type == "excel":
            return self._export_to_excel_generic(report_data)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2) -> str:
        if value is None: return ""
        if not isinstance(value, Decimal): 
            try:
                value = Decimal(str(value))
            except: 
                return "ERR_DEC" # Or handle as appropriate
        return f"{value:,.{places}f}"

    def _export_to_pdf_generic(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story: List[Any] = [] 

        title_text = report_data.get('title', "Financial Report")
        date_desc_text = report_data.get('report_date_description', "")
        
        story.append(Paragraph(title_text, styles['h1']))
        if date_desc_text:
            story.append(Paragraph(date_desc_text, styles['h3']))
        story.append(Spacer(1, 0.5*cm))
        
        table_data_list: List[List[Any]] = [] 

        # Trial Balance specific structure
        if 'debit_accounts' in report_data and 'credit_accounts' in report_data: 
            table_data_list = [["Account Code", "Account Name", "Debit", "Credit"]]
            for acc in report_data.get('debit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            
            totals_row = ["", Paragraph("TOTALS", styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_debits')), styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_credits')), styles['Heading3'])]
            table_data_list.append(totals_row) # type: ignore

        # Balance Sheet / P&L specific structure
        elif 'assets' in report_data or 'revenue' in report_data: 
            headers = ["Section", "Account", "Current Period"]
            if report_data.get('comparative_date') or report_data.get('comparative_start'):
                headers.append("Comparative Period")
            table_data_list = [headers]
            
            sections_map = {
                'assets': 'Assets', 'liabilities': 'Liabilities', 'equity': 'Equity',
                'revenue': 'Revenue', 'expenses': 'Expenses'
            }

            for section_key, section_title in sections_map.items():
                if section_key not in report_data: continue
                section_data = report_data.get(section_key, {})
                table_data_list.append([Paragraph(section_title, styles['h2']), ""] + (["", ""] if len(headers) == 4 else [""])) # Span section title
                
                for acc in section_data.get('accounts', []):
                    row_data = ["", f"{acc['code']} - {acc['name']}", self._format_decimal(acc['balance'])]
                    if len(headers) == 4:
                        comp_val_str = ""
                        if section_data.get('comparative_accounts'):
                            comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                            comp_val_str = self._format_decimal(comp_acc['balance']) if comp_acc else ""
                        row_data.append(comp_val_str)
                    table_data_list.append(row_data)
                
                total_str = self._format_decimal(section_data.get('total'))
                comp_total_str = ""
                if len(headers) == 4:
                     comp_total_str = self._format_decimal(section_data.get('comparative_total')) if section_data.get('comparative_total') is not None else ""
                
                total_row_data = ["", Paragraph(f"Total {section_title}", styles['Heading3']), total_str]
                if len(headers) == 4: total_row_data.append(comp_total_str)
                table_data_list.append(total_row_data)

            if 'net_profit' in report_data: # For P&L
                net_profit_str = self._format_decimal(report_data.get('net_profit'))
                comp_net_profit_str = ""
                if len(headers) == 4:
                    comp_net_profit_str = self._format_decimal(report_data.get('comparative_net_profit')) if report_data.get('comparative_net_profit') is not None else ""
                
                net_profit_row_data = ["", Paragraph("Net Profit/(Loss)", styles['Heading2']), net_profit_str]
                if len(headers) == 4: net_profit_row_data.append(comp_net_profit_str)
                table_data_list.append(net_profit_row_data)

        else:
            story.append(Paragraph("Report data structure not recognized for detailed PDF export.", styles['Normal']))

        if table_data_list and len(table_data_list) > 1 : # Ensure there's data beyond headers
            table = Table(table_data_list, colWidths=[doc.width/len(table_data_list[0])]*len(table_data_list[0])) 
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (2,1), (-1,-1), 'RIGHT'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('LEFTPADDING', (0,0), (-1,-1), 3), 
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                # Span section titles
                ('SPAN', (0,1), (1,1)), # Example for first section title if it's in row 1 (index after header)
                # This needs to be dynamic based on where section titles appear
            ]))
            story.append(table)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _export_to_excel_generic(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active 
        
        title = report_data.get('title', "Financial Report")
        ws.title = title[:30] # type: ignore

        row_num = 1
        ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=14) # type: ignore
        row_num += 1
        date_desc = report_data.get('report_date_description', "")
        if date_desc:
            ws.cell(row=row_num, column=1, value=date_desc).font = Font(italic=True) # type: ignore
            row_num += 1
        row_num += 1 

        if 'debit_accounts' in report_data and 'credit_accounts' in report_data: 
            headers = ["Account Code", "Account Name", "Debit", "Credit"]
            for col_num, header_text in enumerate(headers, 1): 
                ws.cell(row=row_num, column=col_num, value=header_text).font = Font(bold=True) # type: ignore
            row_num += 1

            for acc in report_data.get('debit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=3, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            for acc in report_data.get('credit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=4, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            
            row_num +=1 
            ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True) # type: ignore
            ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
            ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore
        
        elif 'assets' in report_data or 'revenue' in report_data:
            headers = ["Section/Account Code", "Account Name", "Current Period"]
            has_comparative = report_data.get('comparative_date') or report_data.get('comparative_start')
            if has_comparative:
                headers.append("Comparative Period")
            
            for col_num, header_text in enumerate(headers, 1):
                ws.cell(row=row_num, column=col_num, value=header_text).font = Font(bold=True) # type: ignore
            row_num += 1

            sections_map = {
                'assets': 'Assets', 'liabilities': 'Liabilities', 'equity': 'Equity',
                'revenue': 'Revenue', 'expenses': 'Expenses'
            }
            for section_key, section_title in sections_map.items():
                if section_key not in report_data: continue
                section_data = report_data.get(section_key, {})
                
                ws.cell(row=row_num, column=1, value=section_title).font = Font(bold=True, size=12) # type: ignore
                row_num += 1

                for acc in section_data.get('accounts', []):
                    ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                    ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                    ws.cell(row=row_num, column=3, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                    if has_comparative:
                        comp_val = ""
                        if section_data.get('comparative_accounts'):
                            comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                            if comp_acc and comp_acc['balance'] is not None:
                                comp_val = float(comp_acc['balance'])
                        ws.cell(row=row_num, column=4, value=comp_val).number_format = '#,##0.00' # type: ignore
                    row_num += 1
                
                ws.cell(row=row_num, column=2, value=f"Total {section_title}").font = Font(bold=True) # type: ignore
                total_val = section_data.get('total')
                ws.cell(row=row_num, column=3, value=float(total_val) if total_val is not None else "").font = Font(bold=True) # type: ignore
                ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
                if has_comparative:
                    comp_total_val = section_data.get('comparative_total')
                    ws.cell(row=row_num, column=4, value=float(comp_total_val) if comp_total_val is not None else "").font = Font(bold=True) # type: ignore
                    ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore
                row_num += 1
            
            if 'net_profit' in report_data: # For P&L
                row_num += 1
                ws.cell(row=row_num, column=2, value="Net Profit/(Loss)").font = Font(bold=True, size=12) # type: ignore
                net_profit_val = report_data.get('net_profit')
                ws.cell(row=row_num, column=3, value=float(net_profit_val) if net_profit_val is not None else "").font = Font(bold=True) # type: ignore
                ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
                if has_comparative:
                    comp_net_profit_val = report_data.get('comparative_net_profit')
                    ws.cell(row=row_num, column=4, value=float(comp_net_profit_val) if comp_net_profit_val is not None else "").font = Font(bold=True) # type: ignore
                    ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore

        else:
            ws.cell(row=row_num, column=1, value="Report data structure not recognized for Excel export.") # type: ignore

        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            current_width = ws.column_dimensions[column_letter].width # type: ignore
            if current_width == 0: # openpyxl default if not set
                 ws.column_dimensions[column_letter].width = 20 # type: ignore
            else: # Auto size might make it too wide, or too narrow if default value was used.
                ws.column_dimensions[column_letter].auto_size = True # type: ignore
            
        excel_bytes_io = BytesIO()
        wb.save(excel_bytes_io)
        excel_bytes = excel_bytes_io.getvalue()
        excel_bytes_io.close()
        return excel_bytes

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
# app/business_logic/__init__.py
from .customer_manager import CustomerManager
from .vendor_manager import VendorManager
from .product_manager import ProductManager
from .sales_invoice_manager import SalesInvoiceManager # New import

__all__ = [
    "CustomerManager",
    "VendorManager",
    "ProductManager",
    "SalesInvoiceManager", # Added to __all__
]


```

# app/business_logic/sales_invoice_manager.py
```py
# app/business_logic/sales_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime 

from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode

from app.services.business_services import SalesInvoiceService, CustomerService, ProductService
from app.services.core_services import SequenceService
from app.services.tax_service import TaxCodeService 

from app.utils.result import Result
from app.utils.pydantic_models import (
    SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData,
    SalesInvoiceSummaryData, TaxCalculationResultData # Added TaxCalculationResultData
)
from app.tax.tax_calculator import TaxCalculator 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum

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
                 app_core: "ApplicationCore"):
        self.sales_invoice_service = sales_invoice_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.tax_code_service = tax_code_service
        self.tax_calculator = tax_calculator 
        self.sequence_service = sequence_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_and_prepare_invoice_data(
        self, 
        dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData],
        is_update: bool = False # Not actively used yet, but good for context
    ) -> Result[Dict[str, Any]]:
        """
        Validates DTO, fetches related entities, calculates line and header totals.
        Returns a dictionary of validated and calculated data for ORM mapping, or errors.
        """
        errors: List[str] = []
        
        customer = await self.customer_service.get_by_id(dto.customer_id)
        if not customer:
            errors.append(f"Customer with ID {dto.customer_id} not found.")
        elif not customer.is_active:
            errors.append(f"Customer '{customer.name}' (ID: {dto.customer_id}) is not active.")

        # Basic currency validation (assuming currency service is available via app_core for more robust check)
        if not dto.currency_code or len(dto.currency_code) != 3:
            errors.append(f"Invalid currency code: '{dto.currency_code}'.")
        # else:
        #    currency = await self.app_core.currency_service.get_by_id(dto.currency_code)
        #    if not currency or not currency.is_active:
        #        errors.append(f"Currency '{dto.currency_code}' is invalid or not active.")


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

            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product:
                    line_errors_current_line.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active:
                    line_errors_current_line.append(f"Product '{product.name}' is not active on line {i+1}.")
                
                if product: # If product found, use its details if line DTO is missing them
                    if not line_description: line_description = product.name
                    if (unit_price is None or unit_price == Decimal(0)) and product.sales_price is not None:
                        unit_price = product.sales_price
            
            if not line_description: # Description is mandatory
                line_errors_current_line.append(f"Description is required on line {i+1}.")

            if unit_price is None: # Price is mandatory
                line_errors_current_line.append(f"Unit price is required on line {i+1}.")
                unit_price = Decimal(0) # Avoid None for calculations

            # Ensure quantity, unit_price, discount_percent are valid Decimals
            try:
                qty = Decimal(str(line_dto.quantity))
                price = Decimal(str(unit_price))
                discount_pct = Decimal(str(line_dto.discount_percent))
                if qty <= 0: line_errors_current_line.append(f"Quantity must be positive on line {i+1}.")
                if price < 0: line_errors_current_line.append(f"Unit price cannot be negative on line {i+1}.")
                if not (0 <= discount_pct <= 100): line_errors_current_line.append(f"Discount percent must be between 0 and 100 on line {i+1}.")
            except InvalidOperation:
                line_errors_current_line.append(f"Invalid numeric value for quantity, price, or discount on line {i+1}.")
                # Skip further calculation for this line if numbers are bad
                errors.extend(line_errors_current_line)
                continue

            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            line_tax_amount_calc = Decimal(0)
            if line_dto.tax_code:
                # Note: TaxCalculator is stateful with tax_code_service.
                # The manager should pass necessary primitive values or simple DTOs if TaxCalculator is truly generic.
                # Or, TaxCalculator can be instantiated per call if needed.
                # Current TaxCalculator takes tax_code_service in init.
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(
                    amount=line_subtotal_before_tax,
                    tax_code_str=line_dto.tax_code,
                    transaction_type="SalesInvoiceLine" 
                )
                line_tax_amount_calc = tax_calc_result.tax_amount
                # Check if tax_code was valid via TaxCalculator's result or directly
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0):
                    # This implies an issue, possibly tax code not found by calculator's service
                    tc_check = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check or not tc_check.is_active:
                        line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            
            invoice_subtotal_calc += line_subtotal_before_tax
            invoice_total_tax_calc += line_tax_amount_calc
            
            if line_errors_current_line:
                errors.extend(line_errors_current_line)
            
            # This dictionary is for creating SalesInvoiceLine ORM objects
            calculated_lines_for_orm.append({
                "product_id": line_dto.product_id, "description": description,
                "quantity": qty, "unit_price": price,
                "discount_percent": discount_pct,
                "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_subtotal": line_subtotal_before_tax.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "tax_code": line_dto.tax_code, "tax_amount": line_tax_amount_calc, 
                "line_total": (line_subtotal_before_tax + line_tax_amount_calc).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "dimension1_id": line_dto.dimension1_id, "dimension2_id": line_dto.dimension2_id,
            })

        if errors:
            return Result.failure(errors)

        invoice_grand_total = invoice_subtotal_calc + invoice_total_tax_calc

        return Result.success({
            "header_dto": dto, "calculated_lines_for_orm": calculated_lines_for_orm,
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
                invoice_orm.lines.append(SalesInvoiceLine(line_number=i + 1, **line_data_dict))
            
            saved_invoice = await self.sales_invoice_service.save(invoice_orm)
            return Result.success(saved_invoice)
        except Exception as e:
            self.logger.error(f"Error creating draft sales invoice: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred creating sales invoice: {str(e)}"])

    async def update_draft_invoice(self, invoice_id: int, dto: SalesInvoiceUpdateData) -> Result[SalesInvoice]:
        # This method should handle the entire unit of work transactionally.
        async with self.app_core.db_manager.session() as session: 
            existing_invoice = await session.get(SalesInvoice, invoice_id, options=[selectinload(SalesInvoice.lines)])
            if not existing_invoice: return Result.failure([f"Sales Invoice ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only draft invoices can be updated. Current status: {existing_invoice.status}"])

            # Validations involving DB reads (customer, product, tax_code) should ideally happen
            # before or within the same transaction, but _validate_and_prepare_invoice_data
            # currently uses service calls which open their own sessions. This is a potential area for refinement
            # if strict atomicity for these reads is needed alongside the update. For now, this is acceptable.
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
                
                # Efficiently replace lines: delete old, add new
                for line_orm_to_delete in list(existing_invoice.lines): await session.delete(line_orm_to_delete)
                await session.flush() # Process deletions
                # existing_invoice.lines.clear() # Not needed if explicitly deleting

                new_lines_orm: List[SalesInvoiceLine] = []
                for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                    new_lines_orm.append(SalesInvoiceLine(line_number=i + 1, **line_data_dict))
                existing_invoice.lines = new_lines_orm # Assign new list, SQLAlchemy handles relationships
                
                # session.add(existing_invoice) is not strictly necessary if existing_invoice is already managed by this session
                # and modified. But it's harmless.
                
                # Commit is handled by the 'async with session:' block upon exiting successfully.
                # Refreshing after commit is usually done if the object is used immediately after.
                # The service.save() handles its own transaction, so we make this manager method transactional.
                await session.flush()
                await session.refresh(existing_invoice)
                if existing_invoice.lines:
                    await session.refresh(existing_invoice, attribute_names=['lines'])
                    # for line in existing_invoice.lines: await session.refresh(line) # Not strictly needed if lines are fully populated

                return Result.success(existing_invoice)
            except Exception as e:
                self.logger.error(f"Error updating draft sales invoice ID {invoice_id}: {e}", exc_info=True)
                # Rollback handled by session context manager
                return Result.failure([f"An unexpected error occurred while updating sales invoice: {str(e)}"])


    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[SalesInvoice]:
        try:
            return await self.sales_invoice_service.get_by_id(invoice_id)
        except Exception as e:
            self.logger.error(f"Error fetching invoice ID {invoice_id} for dialog: {e}", exc_info=True)
            return None

    async def post_invoice(self, invoice_id: int, user_id: int) -> Result[SalesInvoice]:
        # ... (Placeholder logic from previous version) ...
        self.logger.info(f"Attempting to post Sales Invoice ID {invoice_id} by User ID {user_id}.")
        _invoice = await self.sales_invoice_service.get_by_id(invoice_id)
        if not _invoice: return Result.failure([f"Invoice ID {invoice_id} not found."])
        if _invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only Draft invoices can be posted. Current status: {_invoice.status}"])
        return Result.failure(["Posting logic (including Journal Entry creation) not yet implemented."])


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

