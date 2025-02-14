"""update users table

Revision ID: 2c6e5616c811
Revises: 7b5c1e77f288
Create Date: 2025-02-15 00:55:17.333866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c6e5616c811'
down_revision: Union[str, None] = '7b5c1e77f288'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Меняем тип telegram_id с VARCHAR на Integer
    op.alter_column('users', 'telegram_id',
               existing_type=sa.VARCHAR(),
               type_=sa.Integer(),
               existing_nullable=False)

    op.execute("ALTER TABLE users ALTER COLUMN telegram_id TYPE INTEGER USING telegram_id::INTEGER")
    
    # Добавляем уникальный индекс (даём ему имя)
    op.create_unique_constraint('uq_users_telegram_id', 'users', ['telegram_id'])


def downgrade() -> None:
    # Удаляем ограничение по уникальности
    op.drop_constraint('uq_users_telegram_id', 'users', type_='unique')

    # Возвращаем тип telegram_id обратно в VARCHAR
    op.alter_column('users', 'telegram_id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
