from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy import DefaultClause, text
from sqlalchemy.dialects.postgresql import UUID

from core.settings import config
from db.pg import db


@dataclass
class SocialAccount(db.Model):
    __tablename__ = 'social_accounts'

    __table_args__ = {'schema': config.pg_schema}

    social_account_id: str = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=DefaultClause(text('gen_random_uuid()'))
    )
    user_id: str = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f'{config.pg_schema}.users.user_id'),
        nullable=False
    )
    social_id: str = db.Column(db.String, nullable=False)
    social_provider: str = db.Column(db.String, nullable=False)


class SocialSignupResult(BaseModel):
    username: str
    password: str
    email: str
    access_token: str
    refresh_token: str
