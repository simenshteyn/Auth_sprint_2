from dataclasses import dataclass

from core.settings import config
from db.pg import db
from pydantic import BaseModel
from sqlalchemy import DefaultClause, text
from sqlalchemy.dialects.postgresql import UUID


@dataclass
class Permission(db.Model):
    __tablename__ = 'permissions'

    __table_args__ = {'schema': config.pg_schema}

    permission_id: str = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=DefaultClause(text('gen_random_uuid()'))
    )
    permission_name: str = db.Column(db.String, unique=True, nullable=False)


class PermissionSetRequest(BaseModel):
    permission_uuid: str


class PermissionCreationRequest(BaseModel):
    permission_name: str
