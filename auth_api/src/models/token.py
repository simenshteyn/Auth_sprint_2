from core.settings import config
from db.pg import db
from sqlalchemy import DefaultClause, FetchedValue, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class Token(db.Model):
    query: db.Query  # added for type hinting
    __tablename__ = 'tokens'
    __table_args__ = {'schema': config.pg_schema}

    token_id = db.Column(UUID,
                         primary_key=True,
                         server_default=DefaultClause(
                             text('gen_random_uuid()')))

    token_owner_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f'{config.pg_schema}.users.user_id'),
        nullable=False)
    token_value = db.Column(db.String, nullable=False)
    token_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    expires_at = db.Column(db.DateTime(timezone=True),
                           nullable=False,
                           server_default=FetchedValue())

    def __repr__(self):
        return f'<Token {self.token_owner_id, self.token_value}>'
