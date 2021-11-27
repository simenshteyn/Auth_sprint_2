from dataclasses import dataclass

from core.settings import config
from db.pg import db
from sqlalchemy import DefaultClause, text
from sqlalchemy.dialects.postgresql import UUID


@dataclass
class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    __table_args__ = {'schema': config.pg_schema}

    role_permission_id: str = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=DefaultClause(text('gen_random_uuid()'))
    )
    role_id: str = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f'{config.pg_schema}.roles.role_id'),
        nullable=False
    )
    permission_id: str = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f'{config.pg_schema}.permissions.permission_id'),
        nullable=False
    )

    def __eq__(self, other):
        return self.role_permission_id == other.role_permission_id

    def __hash__(self):
        return hash(self.role_permission_id)
