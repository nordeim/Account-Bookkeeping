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
