from dataclasses import dataclass

from sqlalchemy import DefaultClause, text
from sqlalchemy.dialects.postgresql import UUID

from core.settings import config
from db.pg import db


@dataclass
class RoleOwner(db.Model):
    __tablename__ = 'roles_owners'

    __table_args__ = {'schema': config.pg_schema}

    role_owner_id: str = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=DefaultClause(text('gen_random_uuid()'))
    )
    owner_id: str = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f'{config.pg_schema}.users.user_id'),
        nullable=False
    )
    role_id: str = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f'{config.pg_schema}.roles.role_id'),
        nullable=False
    )
