"""load users dummy data

Revision ID: 488faa52483e
Revises: f95d13e53aaf
Create Date: 2025-02-08 22:35:59.498252

"""
from typing import Sequence, Union
import datetime
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '488faa52483e'
down_revision: Union[str, None] = 'f95d13e53aaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    users = [
        {'name': 'Paul', 'last_name': 'Tapia', 'email': 'paul@tinkin.one',
            'password': 'password123', 'created_at': datetime.datetime.utcnow()},
        {'name': 'Christoph', 'last_name': 'Veloz', 'email': 'christoph@joinkamina.com',
            'password': 'password456', 'created_at': datetime.datetime.utcnow()},
        {'name': 'Leo', 'last_name': 'Tiguan', 'email': 'leonardo@joinkamina.com',
            'password': 'password789', 'created_at': datetime.datetime.utcnow()},
        {'name': 'Dennis', 'last_name': 'Espin', 'email': 'dennis@tinkin.one',
            'password': 'password101', 'created_at': datetime.datetime.utcnow()},
        {'name': 'Facu', 'last_name': 'Velazo', 'email': 'facundo@tinkin.one',
            'password': 'password202', 'created_at': datetime.datetime.utcnow()},
        {'name': 'Anto', 'last_name': 'Gallego', 'email': 'aperez@tinkin.one',
            'password': 'password303', 'created_at': datetime.datetime.utcnow()},
    ]

    for user in users:
        op.execute(sa.text("""
            INSERT INTO users (name, last_name, email, password, created_at) 
            VALUES (:name, :last_name, :email, :password, :created_at)
        """).bindparams(name=user['name'], last_name=user['last_name'], email=user['email'], password=user['password'], created_at=user['created_at']))


def downgrade() -> None:
    op.execute("""
        DELETE FROM users 
    """)
