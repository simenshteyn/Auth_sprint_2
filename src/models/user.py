from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import DefaultClause, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.settings import config
from db.pg import db


class User(db.Model):
    query: db.Query  # added for type hinting
    __tablename__ = 'users'
    __table_args__ = {'schema': config.pg_schema}

    user_id = db.Column(UUID(as_uuid=True),
                        primary_key=True,
                        server_default=DefaultClause(
                            text('gen_random_uuid()')))
    user_login = db.Column(db.String,
                           unique=True,
                           nullable=False)
    user_password = db.Column(db.String,
                              nullable=False)
    user_email = db.Column(db.String,
                           unique=True,
                           nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True),
                           onupdate=func.now())

    def __repr__(self):
        return f'<User {self.user_login}>'


class LoginRequest(BaseModel):
    username: constr(min_length=1, strip_whitespace=True, to_lower=True)
    password: constr(min_length=1, strip_whitespace=True)


class SignupRequest(LoginRequest):
    email: EmailStr


class ModifyRequest(LoginRequest):
    pass


class UserRoleAssignRequest(BaseModel):
    role_uuid: str
