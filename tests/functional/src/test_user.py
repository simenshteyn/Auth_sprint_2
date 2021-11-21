import random
import string

import pytest
import requests
from psycopg2._psycopg import connection, cursor
from pydantic import BaseModel, constr
from redis import Redis
from requests import Response

from tests.functional.settings import config


def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_base_url(endpoint):
    return '{protocol}://{host}:{port}/api/v{api_version}/{endpoint}'.format(
        protocol=config.service_protocol,
        host=config.service_host,
        port=config.service_port,
        api_version=config.service_api_version,
        endpoint=endpoint
    )


def json_api_request(http_method: str,
                     endpoint: str,
                     json_data: dict,
                     headers: dict = None) -> Response:
    response = requests.request(http_method,
                                get_base_url(endpoint),
                                json=json_data,
                                headers=headers)
    try:
        response.json()
        return response
    except ValueError:
        pytest.fail("Non-json response from the endpoint: "
                    + response.text)


class AuthTokenResponse(BaseModel):
    """Represents the structure of successful auth response,
    validates presence and correct formatting of fields"""
    access_token: constr(min_length=1)
    refresh_token: constr(min_length=1)


@pytest.fixture(scope='session')
def valid_user():
    pass


def create_user(user_data: dict,
                pg_curs: cursor,
                redis_conn) -> tuple[Response, dict]:
    """Helper routine for user creation
    to be reused by multiple tests.
    Returns the api response and
    the resulting user representation in the database"""
    response = json_api_request("post", "user/signup", user_data)
    response_json = response.json()
    if not response.status_code == 200:
        return response, {}
    try:
        token_response = AuthTokenResponse(**response_json)
    except ValueError as err:
        pytest.fail(err)
        return

    query = "select user_id,user_login,user_email " \
            "from app.users where user_login=%s"
    pg_curs.execute(query, (user_data['username'],))
    users = dictfetchall(pg_curs)

    assert len(users), "User not found in the database after adding"
    assert len(users) == 1, \
        "Not a single record found after adding a user"

    #
    # Test access token is found in redis
    #
    saved_access_token = redis_conn.get(name=token_response.access_token)
    assert saved_access_token.decode() == "", "Access token not found"

    return response, users[0]


class TestUser:
    def test_create_user(self, pg_conn: connection,
                         pg_curs: cursor,
                         redis_conn: Redis):
        username = password = "".join(
            random.choices(string.ascii_lowercase, k=10))
        email = username + "@yandex.com"

        valid_data = {
            "username": username, "password": password, "email": email
        }

        #
        # Field requirements satisfaction
        #
        for missing_field in ["username", "password", "email"]:
            partial_data = {k: valid_data[k]
                            for k in valid_data
                            if not k == missing_field}
            # response = json_api_request("post", "user/signup", partial_data)
            response, _ = create_user(partial_data, pg_curs, redis_conn)
            assert 400 <= response.status_code < 500, \
                f"Invalid response code when {missing_field} is missing"

            response_json = response.json()
            expected_error_code = f"{missing_field.upper()}_MISSING"
            assert response_json["error_code"] == expected_error_code, \
                f"Invalid error_code when {missing_field} is missing"

        #
        # Successful creation of a user
        #
        create_response, user = create_user(valid_data, pg_curs, redis_conn)
        assert create_response.status_code == 200, \
            f"Invalid response code when creating user, " \
            f"response text: {response.text}"
        assert user["user_login"] == valid_data["username"], \
            "Wrong username after adding a user"
        assert user["user_email"] == valid_data["email"], \
            "Wrong email after adding a user"

        #
        # Inability to create duplicated users
        #
        # response = json_api_request("post", "user/signup", valid_data)
        # response.json()
        _, duplicated_user = create_user(valid_data, pg_curs, redis_conn)
        assert response.status_code == 400, \
            "Non-error response code when creating a duplicated user"

        # TODO: use teardown of figure out if its possible to use t
        #  ransactions
        query = "delete from app.users where user_id=%s"
        pg_curs.execute(query, (user['user_id'],))
        pg_conn.commit()

    def test_login_user(self, pg_conn: connection,
                        pg_curs: cursor,
                        redis_conn: Redis):

        username = password = "".join(
            random.choices(string.ascii_lowercase, k=10))
        email = username + "@yandex.com"

        valid_data = {
            "username": username, "password": password, "email": email
        }

        response, user = create_user(valid_data, pg_curs, redis_conn)

        del valid_data["email"]
        response = json_api_request("post", "user/auth", valid_data)

        try:
            token_response = AuthTokenResponse(**response.json())
        except ValueError as err:
            pytest.fail(err)
            return

        query = ("select token_id, token_owner_id, token_value "
                 "from app.tokens where token_owner_id=%s and token_value=%s"
                 "")
        pg_curs.execute(query,
                        (user["user_id"], token_response.refresh_token,))
        access_tokens = dictfetchall(pg_curs)
        assert len(access_tokens) == 1, \
            "None or multiple refresh tokens found " \
            f"for logged in user: {len(access_tokens)}"

        db_token = access_tokens[0]['token_value']
        expected = token_response.refresh_token
        assert db_token == expected, "Refresh token in the DB is incorrect"

        #
        # access token is there
        #
        saved_access_token = redis_conn.get(name=token_response.access_token)
        assert saved_access_token.decode() == "", "Access token not found"

        # Can't login with a wrong password
        wrong_data = {**valid_data, "password": "123456"}
        response = json_api_request("post", "user/auth", wrong_data)
        assert response.status_code == 400, \
            "No error when using wrong password"
        assert response.json()['error_code'] == 'WRONG_PASSWORD'

        # Can't login with a wrong username
        wrong_data = {**valid_data, "username": "123456"}
        response = json_api_request("post", "user/auth", wrong_data)
        assert response.status_code == 400, \
            "No error when using wrong password"
        assert response.json()['error_code'] == 'USER_NOT_FOUND'

        # TODO: use teardown of figure out if its possible to use t
        #  ransactions
        query = "delete from app.users where user_id=%s"
        pg_curs.execute(query, (user['user_id'],))
        pg_conn.commit()

    def test_token_refresh(self, pg_conn: connection,
                           pg_curs: cursor,
                           redis_conn: Redis):

        username = password = "".join(
            random.choices(string.ascii_lowercase, k=10))
        email = username + "@yandex.com"

        valid_data = {
            "username": username, "password": password, "email": email
        }

        response, user = create_user(valid_data, pg_curs, redis_conn)

        response_json = response.json()
        refresh_token = response_json['refresh_token']
        headers = {
            'Authorization': 'Bearer ' + refresh_token
        }
        response = json_api_request('PUT', 'user/auth', {}, headers)
        response_json = response.json()
        assert "access_token" in response_json, "No access_token in response"
        assert "refresh_token" in response_json, "No refresh_token in response"

        # TODO: make a request to endpoint requiring auth
        #  and make sure it works (when we'll have such an endpoint)

        # TODO: use teardown of figure out if its possible to use t
        #  ransactions
        query = "delete from app.users where user_id=%s"
        pg_curs.execute(query, (user['user_id'],))
        pg_conn.commit()

    def test_logout(self, pg_conn: connection,
                    pg_curs: cursor,
                    redis_conn: Redis):
        username = password = "".join(
            random.choices(string.ascii_lowercase, k=10))
        email = username + "@yandex.com"

        valid_data = {
            "username": username, "password": password, "email": email
        }

        response, user = create_user(valid_data, pg_curs, redis_conn)

        response_json = response.json()

        access_token = response_json['access_token']
        headers = {
            'Authorization': 'Bearer ' + access_token
        }

        response = json_api_request('POST',
                                    'user/auth/logout',
                                    response_json,
                                    headers)
        response_json = response.json()

        assert response.status_code == 200, "Invalid response code on logout"

        # Make sure the access token is no longer accepted
        # by an authorized endpoint (logout).
        response = json_api_request('POST',
                                    'user/auth/logout',
                                    response_json,
                                    headers)

        assert response.status_code == 401, \
            "Invalid response code when making unauthenticated request"
        assert response.json().get("error_code") == "ACCESS_TOKEN_EXPIRED", \
            "Invalid error_code when making unauthenticated request"

    # TODO: combine login, refresh, logout into a single flow test

    def test_modify(self, pg_conn: connection,
                    pg_curs: cursor,
                    redis_conn: Redis):
        username = password = "".join(
            random.choices(string.ascii_lowercase, k=10))
        email = username + "@yandex.com"

        valid_data = {
            "username": username, "password": password, "email": email
        }

        response, user = create_user(valid_data, pg_curs, redis_conn)

        response_json = response.json()

        access_token = response_json['access_token']
        headers = {
            'Authorization': 'Bearer ' + access_token
        }

        del valid_data["email"]
        modified_data = {k: valid_data[k] + "1" for k in valid_data}

        response = json_api_request('PATCH',
                                    'user/auth',
                                    modified_data,
                                    headers)
        assert response.status_code == 202, \
            "Credentials change wasn't accepted"

        query = "select user_login,user_password " \
                "from app.users where user_id=%s"
        pg_curs.execute(query, (user['user_id'],))
        user = dictfetchall(pg_curs).pop()

        assert user["user_login"] == modified_data["username"], \
            "username didn't change in the database"
        assert user["user_password"] == modified_data["password"], \
            "password didn't change in the database"

    def test_history(self, pg_curs: cursor,
                     redis_conn: Redis):
        username = password = "".join(
            random.choices(string.ascii_lowercase, k=10))
        email = username + "@yandex.com"

        valid_data = {
            "username": username, "password": password, "email": email
        }

        response, user = create_user(valid_data, pg_curs, redis_conn)

        response_json = response.json()

        access_token = response_json['access_token']
        headers = {
            'Authorization': 'Bearer ' + access_token
        }

        del valid_data["email"]
        json_api_request("post", "user/auth", valid_data)

        response = json_api_request('GET', 'user/auth', {}, headers)

        assert len(response.json()) > 0, "No history events found"
