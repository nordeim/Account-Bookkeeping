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
