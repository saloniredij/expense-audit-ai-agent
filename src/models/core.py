import uuid
from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    accounts: Mapped[List["BankAccount"]] = relationship(
        "BankAccount", back_populates="user", cascade="all, delete-orphan"
    )
    reports: Mapped[List["AuditReport"]] = relationship(
        "AuditReport", back_populates="user", cascade="all, delete-orphan"
    )

from sqlalchemy import ForeignKey

class BankAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bank_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    mask: Mapped[str] = mapped_column()
    institution_name: Mapped[str] = mapped_column()

    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )
    
class Transaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transactions"

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bank_accounts.id"), index=True)
    external_id: Mapped[str] = mapped_column(unique=True, index=True)
    date: Mapped[str] = mapped_column(index=True) # YYYY-MM-DD
    amount: Mapped[float] = mapped_column()
    merchant_name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    
    account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="transactions")
