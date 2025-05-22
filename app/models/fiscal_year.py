# File: app/models/fiscal_year.py
# New model for accounting.fiscal_years
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import DATERANGE
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.sql import literal_column
from app.models.base import Base, TimestampMixin, UserAuditMixin
# from app.models.user import User # For FKs
import datetime
from typing import List, Optional

# For EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
# This requires a bit more setup if using pure SQLAlchemy types for DATERANGE.
# For now, the DB schema itself enforces this. SQLAlchemy model won't explicitly model the EXCLUDE constraint
# but the DB will enforce it.

class FiscalYear(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'fiscal_years'
    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='fy_date_range_check'),
        # The EXCLUDE constraint is complex for ORM, rely on DB schema.
        # UniqueConstraint('year_name', name='uq_fiscal_years_year_name'), # Already unique in col def
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[Optional[int]] = mapped_column("closed_by", Integer, ForeignKey('core.users.id'), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin

    # Relationships
    # closed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[closed_by_user_id])
    fiscal_periods: Mapped[List["FiscalPeriod"]] = relationship("FiscalPeriod", back_populates="fiscal_year") # type: ignore
    budgets: Mapped[List["Budget"]] = relationship("Budget", back_populates="fiscal_year_obj") # type: ignore
