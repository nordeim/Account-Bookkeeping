# File: app/models/core/company_setting.py
# (Moved from app/models/company_setting.py and fields updated)
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.core.user import User # For FK relationship type hint
import datetime
from typing import Optional

class CompanySetting(Base, TimestampMixin):
    __tablename__ = 'company_settings'
    __table_args__ = (
        CheckConstraint("fiscal_year_start_month BETWEEN 1 AND 12", name='ck_cs_fy_month'),
        CheckConstraint("fiscal_year_start_day BETWEEN 1 AND 31", name='ck_cs_fy_day'),
        {'schema': 'core'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True) 
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registration_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[str] = mapped_column(String(50), default='Singapore') 
    country: Mapped[str] = mapped_column(String(50), default='Singapore') 
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logo: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1) 
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, default=1) 
    base_currency: Mapped[str] = mapped_column(String(3), default='SGD') 
    tax_id_label: Mapped[str] = mapped_column(String(50), default='UEN') 
    date_format: Mapped[str] = mapped_column(String(20), default='yyyy-MM-dd') 
    
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True) 

    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])
