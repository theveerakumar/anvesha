import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class FundRating(Base):
    __tablename__ = "fund_ratings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scheme_code: Mapped[int] = mapped_column(Integer, index=True)
    star_rating: Mapped[int] = mapped_column(Integer)
    overall_score: Mapped[float] = mapped_column(Float)
    performance_score: Mapped[float | None] = mapped_column(Float)
    consistency_score: Mapped[float | None] = mapped_column(Float)
    risk_score: Mapped[float | None] = mapped_column(Float)
    cost_score: Mapped[float | None] = mapped_column(Float)
    portfolio_quality_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FundRecommendation(Base):
    __tablename__ = "fund_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scheme_code: Mapped[int] = mapped_column(Integer, index=True)
    recommendation: Mapped[str] = mapped_column(String(50))
    confidence_score: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(Text)
    strengths: Mapped[str | None] = mapped_column(Text)
    weaknesses: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FundHolding(Base):
    __tablename__ = "fund_holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scheme_code: Mapped[int] = mapped_column(Integer, index=True)
    stock_name: Mapped[str] = mapped_column(String(200))
    sector: Mapped[str | None] = mapped_column(String(100))
    weight: Mapped[float] = mapped_column(Float)
    market_cap: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RecommendationAuditLog(Base):
    __tablename__ = "recommendation_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scheme_code: Mapped[int] = mapped_column(Integer, index=True)
    scheme_name: Mapped[str | None] = mapped_column(String(500))
    recommendation: Mapped[str] = mapped_column(String(50))
    confidence_score: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str | None] = mapped_column(String(50))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
