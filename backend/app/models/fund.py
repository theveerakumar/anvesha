import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Fund(Base):
    __tablename__ = "funds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scheme_code: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    scheme_name: Mapped[str] = mapped_column(String(500), index=True)
    amc: Mapped[str | None] = mapped_column(String(200))
    scheme_type: Mapped[str | None] = mapped_column(String(100))
    scheme_category: Mapped[str | None] = mapped_column(String(200), index=True)
    fund_family: Mapped[str | None] = mapped_column(String(200))
    isin: Mapped[str | None] = mapped_column(String(20))
    isin_growth: Mapped[str | None] = mapped_column(String(20))
    nav: Mapped[float | None] = mapped_column(Float)
    nav_date: Mapped[date | None] = mapped_column(Date)
    aum_cr: Mapped[float | None] = mapped_column(Float)
    expense_ratio: Mapped[float | None] = mapped_column(Float)
    fund_manager: Mapped[str | None] = mapped_column(String(500))
    risk_level: Mapped[str | None] = mapped_column(String(50))
    return_1y: Mapped[float | None] = mapped_column(Float)
    return_3y: Mapped[float | None] = mapped_column(Float)
    return_5y: Mapped[float | None] = mapped_column(Float)
    benchmark: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    nav_history: Mapped[list["FundNAVHistory"]] = relationship(
        back_populates="fund", cascade="all, delete-orphan"
    )


class FundNAVHistory(Base):
    __tablename__ = "fund_nav_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fund_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funds.id", ondelete="CASCADE"), index=True
    )
    nav_date: Mapped[date] = mapped_column(Date, index=True)
    nav: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    fund: Mapped["Fund"] = relationship(back_populates="nav_history")

    __table_args__ = (
        UniqueConstraint("fund_id", "nav_date", name="ix_fund_nav_history_fund_date"),
    )
