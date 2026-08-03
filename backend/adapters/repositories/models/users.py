from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseUsers(DeclarativeBase):
    pass


class User(BaseUsers):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roles: Mapped[List["Role"]] = relationship(secondary="user_roles", back_populates="users")

    __table_args__ = (
        Index("idx_users_tenant_id", "tenant_id"),
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
        Index("idx_users_branch_id", "branch_id"),
    )


class Role(BaseUsers):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    users: Mapped[List["User"]] = relationship(secondary="user_roles", back_populates="roles")


class UserRoleAssociation(BaseUsers):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
