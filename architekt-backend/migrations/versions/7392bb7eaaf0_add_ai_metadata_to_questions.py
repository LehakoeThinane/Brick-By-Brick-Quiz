"""Add ai_metadata to questions

Revision ID: 7392bb7eaaf0
Revises: e15a1c6406c6
Create Date: 2026-04-16 12:00:51.631746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7392bb7eaaf0'
down_revision: Union[str, Sequence[str], None] = 'e15a1c6406c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    op.add_column('questions', sa.Column('ai_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('questions', 'ai_metadata')
