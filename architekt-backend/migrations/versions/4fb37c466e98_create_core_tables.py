"""create core tables

Revision ID: 4fb37c466e98
Revises:
Create Date: 2026-04-16 09:13:42.467583

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "4fb37c466e98"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    question_type = sa.Enum(
        "definition",
        "scenario",
        "tradeoff",
        "identification",
        name="question_type",
    )
    question_source = sa.Enum("manual", "ai_generated", name="question_source")
    review_status = sa.Enum("draft", "approved", "retired", name="review_status")
    quiz_mode = sa.Enum("category", "adaptive", "review", name="quiz_mode")
    quiz_session_status = sa.Enum("active", "completed", "expired", name="quiz_session_status")
    mastery_signal = sa.Enum("STRONG", "PARTIAL", "WEAK", "MISS", name="mastery_signal")
    mastery_state = sa.Enum(
        "UNSEEN",
        "ATTEMPTED",
        "STRUGGLING",
        "DEVELOPING",
        "COMPETENT",
        "MASTERED",
        name="mastery_state",
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("difficulty", sa.SmallInteger(), nullable=True),
        sa.Column("question_type", question_type, nullable=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct_answer", sa.String(length=10), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column("related_concepts", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("source", question_source, nullable=True),
        sa.Column("review_status", review_status, nullable=True),
        sa.Column("times_answered", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("times_correct", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quiz_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mode", quiz_mode, nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", quiz_session_status, nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "answer_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question_version", sa.Integer(), nullable=False),
        sa.Column("submitted_answer", sa.String(length=10), nullable=False),
        sa.Column("correct_answer", sa.String(length=10), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column("mastery_signal", mastery_signal, nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["quiz_sessions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "mastery_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mastery_state", mastery_state, nullable=True),
        sa.Column("total_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("rolling_accuracy", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("avg_response_time_ms", sa.Integer(), nullable=True),
        sa.Column("consecutive_correct", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_attempted_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "review_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("priority_score", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("review_queue")
    op.drop_table("mastery_profiles")
    op.drop_table("answer_attempts")
    op.drop_table("quiz_sessions")
    op.drop_table("questions")
    op.drop_table("categories")
    op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(
        "UNSEEN",
        "ATTEMPTED",
        "STRUGGLING",
        "DEVELOPING",
        "COMPETENT",
        "MASTERED",
        name="mastery_state",
    ).drop(bind, checkfirst=True)
    sa.Enum("STRONG", "PARTIAL", "WEAK", "MISS", name="mastery_signal").drop(bind, checkfirst=True)
    sa.Enum("active", "completed", "expired", name="quiz_session_status").drop(bind, checkfirst=True)
    sa.Enum("category", "adaptive", "review", name="quiz_mode").drop(bind, checkfirst=True)
    sa.Enum("draft", "approved", "retired", name="review_status").drop(bind, checkfirst=True)
    sa.Enum("manual", "ai_generated", name="question_source").drop(bind, checkfirst=True)
    sa.Enum("definition", "scenario", "tradeoff", "identification", name="question_type").drop(
        bind,
        checkfirst=True,
    )
