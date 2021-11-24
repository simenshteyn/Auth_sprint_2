import textwrap

from tests.functional.settings import config


def test_db_connection(pg_conn):
    is_connected = bool(pg_conn and pg_conn.closed == 0)
    assert is_connected


def table_exists(pg_curs, id_name: str, table_name: str,
                 scheme: str = config.pg_schema) -> bool:
    statement = textwrap.dedent(
        f'SELECT {id_name} FROM {scheme}.{table_name};'
    )
    pg_curs.execute(statement)
    if len(pg_curs.fetchall()) >= 0:
        return True
    else:
        return False


def get_enum_len(pg_curs, enum_name: str) -> int:
    statement = textwrap.dedent("""
        SELECT type.typname,
               enum.enumlabel AS value
          FROM pg_enum AS enum
          JOIN pg_type AS type
               ON (type.oid = enum.enumtypid)
         WHERE type.typname = %s
         GROUP BY enum.enumlabel, type.typname;
    """)
    pg_curs.execute(statement, (enum_name,))
    return len(pg_curs.fetchall())


def test_db_enum_auth_event_type_exists(pg_curs):
    assert get_enum_len(pg_curs, 'auth_event_type') == 2


def test_db_table_users_exists(pg_curs):
    assert table_exists(pg_curs, 'user_id', 'users')


def test_db_table_auth_events_exists(pg_curs):
    assert table_exists(pg_curs, 'auth_event_id', 'auth_events')


def test_db_table_tokens_exists(pg_curs):
    assert table_exists(pg_curs, 'token_id', 'tokens')


def test_db_table_roles_exists(pg_curs):
    assert table_exists(pg_curs, 'role_id', 'roles')


def test_db_table_permissions_exists(pg_curs):
    assert table_exists(pg_curs, 'permission_id', 'permissions')


def test_db_table_role_permissions_exists(pg_curs):
    assert table_exists(pg_curs, 'role_permission_id', 'role_permissions')


def test_db_table_roles_owners_exists(pg_curs):
    assert table_exists(pg_curs, 'role_owner_id', 'roles_owners')


def test_db_table_social_accounts_exists(pg_curs):
    assert table_exists(pg_curs, 'social_account_id', 'social_accounts')
