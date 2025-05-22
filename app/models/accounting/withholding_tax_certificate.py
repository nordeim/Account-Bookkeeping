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
