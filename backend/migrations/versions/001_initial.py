"""Initial migration: Create funds and fund_nav_history tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "funds",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scheme_code", sa.BigInteger(), nullable=False),
        sa.Column("scheme_name", sa.String(500), nullable=False),
        sa.Column("amc", sa.String(200), nullable=True),
        sa.Column("scheme_type", sa.String(100), nullable=True),
        sa.Column("scheme_category", sa.String(200), nullable=True),
        sa.Column("fund_family", sa.String(200), nullable=True),
        sa.Column("isin", sa.String(20), nullable=True),
        sa.Column("isin_growth", sa.String(20), nullable=True),
        sa.Column("nav", sa.Float(), nullable=True),
        sa.Column("nav_date", sa.Date(), nullable=True),
        sa.Column("aum_cr", sa.Float(), nullable=True),
        sa.Column("expense_ratio", sa.Float(), nullable=True),
        sa.Column("fund_manager", sa.String(500), nullable=True),
        sa.Column("risk_level", sa.String(50), nullable=True),
        sa.Column("return_1y", sa.Float(), nullable=True),
        sa.Column("return_3y", sa.Float(), nullable=True),
        sa.Column("return_5y", sa.Float(), nullable=True),
        sa.Column("benchmark", sa.String(200), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_funds_scheme_code"), "funds", ["scheme_code"], unique=True)
    op.create_index(op.f("ix_funds_scheme_name"), "funds", ["scheme_name"])
    op.create_index(op.f("ix_funds_scheme_category"), "funds", ["scheme_category"])

    op.create_table(
        "fund_nav_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fund_id", sa.UUID(), nullable=False),
        sa.Column("nav_date", sa.Date(), nullable=False),
        sa.Column("nav", sa.Float(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fund_nav_history_fund_id"), "fund_nav_history", ["fund_id"]
    )
    op.create_index(
        op.f("ix_fund_nav_history_nav_date"), "fund_nav_history", ["nav_date"]
    )
    op.create_index(
        "ix_fund_nav_history_fund_date",
        "fund_nav_history",
        ["fund_id", "nav_date"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_fund_nav_history_fund_date", table_name="fund_nav_history")
    op.drop_index(op.f("ix_fund_nav_history_nav_date"), table_name="fund_nav_history")
    op.drop_index(op.f("ix_fund_nav_history_fund_id"), table_name="fund_nav_history")
    op.drop_table("fund_nav_history")
    op.drop_index(op.f("ix_funds_scheme_category"), table_name="funds")
    op.drop_index(op.f("ix_funds_scheme_name"), table_name="funds")
    op.drop_index(op.f("ix_funds_scheme_code"), table_name="funds")
    op.drop_table("funds")
