import textwrap


def get_user_uuid(pg_curs, username: str, table_name: str = 'users',
                  scheme: str = 'app') -> str:
    """Get user uuid from username directly from database. """
    statement = textwrap.dedent(
        f'SELECT user_id FROM {scheme}.{table_name} WHERE user_login = %s ;'
    )
    pg_curs.execute(statement, (username,))
    return pg_curs.fetchone()[0]


def remove_user(pg_curs, user_id: str, table_name: str = 'users',
                scheme: str = 'app') -> None:
    """Remove user with given UUID from database. """
    statement = textwrap.dedent(
        f'DELETE FROM {scheme}.{table_name} WHERE user_id = %s ;'
    )
    pg_curs.execute(statement, (user_id,))


def create_role(pg_curs, role_name: str, table_name: str = 'roles',
                scheme: str = 'app') -> str:
    """Create role in database and return its UUID. """
    statement = textwrap.dedent(f'INSERT INTO {scheme}.{table_name} '
                                f'(role_name) VALUES (%s);')
    pg_curs.execute(statement, (role_name,))

    statement = textwrap.dedent(
        f'SELECT role_id FROM {scheme}.{table_name} WHERE role_name = %s ;'
    )
    pg_curs.execute(statement, (role_name,))
    return pg_curs.fetchone()[0]


def assign_role(pg_curs, owner_id: str, role_id: str,
                table_name: str = 'roles_owners', scheme: str = 'app') -> str:
    """Assign role in database to user directly. """
    statement = textwrap.dedent(f'INSERT INTO {scheme}.{table_name} '
                                f'(owner_id, role_id) VALUES (%s, %s);')
    pg_curs.execute(statement, (owner_id, role_id))
    statement = textwrap.dedent(
        f'SELECT role_owner_id FROM {scheme}.{table_name} '
        f'WHERE owner_id = %s AND role_id = %s ;'
    )
    pg_curs.execute(statement, (owner_id, role_id))
    return pg_curs.fetchone()[0]


def remove_role(pg_curs, role_id: str, table_name: str = 'roles',
                scheme: str = 'app') -> None:
    """Remove user with given UUID from database. """
    statement = textwrap.dedent(
        f'DELETE FROM {scheme}.{table_name} WHERE role_id = %s ;'
    )
    pg_curs.execute(statement, (role_id,))


def get_auth_headers(token: str):
    return {'Authorization': 'Bearer ' + token}
