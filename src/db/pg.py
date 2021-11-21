from flask_sqlalchemy import SQLAlchemy

from core.settings import config

db = SQLAlchemy()

PG_URI = 'postgresql://{pg_user}:{pg_pass}@{pg_host}/{pg_dbname}'.format(
    pg_user=config.pg_user,
    pg_pass=config.pg_pass,
    pg_host=config.pg_host,
    pg_dbname=config.pg_dbname
)
