from core.settings import config
from db.pg import db
from sqlalchemy import DefaultClause, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class AuthEvent(db.Model):
    query: db.Query  # added for type hinting
    __tablename__ = 'auth_events'
    __table_args__ = {'schema': config.pg_schema}

    auth_event_id: str = db.Column(
        UUID,
        primary_key=True,
        server_default=DefaultClause(text('gen_random_uuid()'))
    )
    auth_event_owner_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(f'{config.pg_schema}.users.user_id'),
        nullable=False)
    auth_event_type = db.Column(db.String, nullable=False)
    auth_event_time = db.Column(db.DateTime(timezone=True),
                                server_default=func.now())
    auth_event_fingerprint = db.Column(db.String, nullable=False)
