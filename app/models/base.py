# File: app/models/base.py
# (Content previously generated, no changes needed)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import DateTime, Integer, ForeignKey # Ensure Integer, ForeignKey are imported
from typing import Optional
import datetime

Base = declarative_base()

class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now())

class UserAuditMixin:
    # Explicitly add ForeignKey references here as UserAuditMixin is generic.
    # The target table 'core.users' is known.
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
