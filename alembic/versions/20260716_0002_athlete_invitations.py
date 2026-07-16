"""Add athlete account status and invitation tokens."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260716_0002"
down_revision: str | None = "20260709_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    status_enum = postgresql.ENUM("pending", "active", "disabled", name="user_status")
    status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("status", status_enum, nullable=True))
    op.execute(
        "UPDATE users SET status = CASE WHEN is_active THEN 'active'::user_status ELSE 'disabled'::user_status END"
    )
    op.alter_column("users", "status", nullable=False, server_default="active")
    op.alter_column("users", "password_hash", existing_type=sa.String(length=512), nullable=True)

    op.create_table(
        "account_invitations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("athlete_reference_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_by_service", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_account_invitations_user_id", "account_invitations", ["user_id"])
    op.create_index("ix_account_invitations_expires_at", "account_invitations", ["expires_at"])
    op.create_index("uq_account_invitations_token_hash", "account_invitations", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_table("account_invitations")
    op.alter_column("users", "password_hash", existing_type=sa.String(length=512), nullable=False)
    op.drop_column("users", "status")
    postgresql.ENUM(name="user_status").drop(op.get_bind(), checkfirst=True)
