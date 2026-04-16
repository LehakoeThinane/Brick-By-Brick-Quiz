"""Add offline sync structures

Revision ID: e15a1c6406c6
Revises: 4fb37c466e98
Create Date: 2026-04-16 11:16:44.195232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e15a1c6406c6'
down_revision: Union[str, Sequence[str], None] = '4fb37c466e98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    sync_status_enum = postgresql.ENUM('PENDING', 'SYNCED', 'FAILED', name='sync_status', create_type=False)
    sync_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add columns to answer_attempts
    op.add_column('answer_attempts', sa.Column('client_attempt_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('answer_attempts', sa.Column('sync_status', sync_status_enum, nullable=True))
    op.add_column('answer_attempts', sa.Column('synced_at', sa.DateTime(), nullable=True))
    op.create_unique_constraint(None, 'answer_attempts', ['client_attempt_id'])

    # 3. Create offline_sync_queue table
    op.create_table('offline_sync_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_attempt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sync_status_enum, nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_attempt_id')
    )


def downgrade() -> None:
    # 1. Drop table
    op.drop_table('offline_sync_queue')
    
    # 2. Drop columns
    op.drop_constraint(None, 'answer_attempts', type_='unique')
    op.drop_column('answer_attempts', 'synced_at')
    op.drop_column('answer_attempts', 'sync_status')
    op.drop_column('answer_attempts', 'client_attempt_id')
    
    # 3. Drop enum types
    sync_status_enum = postgresql.ENUM('PENDING', 'SYNCED', 'FAILED', name='sync_status')
    sync_status_enum.drop(op.get_bind())
