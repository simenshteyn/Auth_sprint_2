from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy import DefaultClause, text
from sqlalchemy.dialects.postgresql import UUID

from core.settings import config
from db.pg import db


@dataclass
class Role(db.Model):
    __tablename__ = 'roles'

    __table_args__ = {'schema': config.pg_schema}

    role_id: str = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=DefaultClause(text('gen_random_uuid()'))
    )
    role_name: str = db.Column(db.String, unique=True, nullable=False)


class RoleCreationRequest(BaseModel):
    role_name: str
