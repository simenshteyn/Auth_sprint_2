from core.settings import config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

PG_URI = 'postgresql://{pg_user}:{pg_pass}@{pg_host}/{pg_dbname}'.format(
    pg_user=config.pg_user,
    pg_pass=config.pg_pass,
    pg_host=config.pg_host,
    pg_dbname=config.pg_dbname
)
