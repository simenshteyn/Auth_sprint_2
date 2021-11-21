import sys
from dataclasses import dataclass
from functools import wraps
from http import HTTPStatus

from flask import jsonify, make_response, request
from flask_jwt_extended import get_jwt
from pydantic import ValidationError

from db.redis_client import redis


@dataclass
class ServiceException(Exception):
    error_code: str
    message: str


# TODO: decide if it worth the effort
def make_service_exception(err: ValidationError):
    """ Transform and instance of pydantic.ValidationError
    into an instance of ServiceException"""
    first_error = err.errors().pop()
    error_field = first_error.get('loc')[0]
    error_reason = first_error.get('type').split('.')[-1]

    error_code = f'{error_field}_{error_reason}'.upper()
    message = f'{error_field} is {error_reason}'

    return ServiceException(error_code, message)


def eprint(*args, **kwargs):
    """Print in server output"""
    print(*args, file=sys.stderr, **kwargs)


def authenticate():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            access_token = request.headers['Authorization'].split().pop(-1)

            if not redis.get(access_token) == b'':
                return make_response(
                    jsonify(error_code='ACCESS_TOKEN_EXPIRED',
                            message='Access token has expired'),
                    HTTPStatus.UNAUTHORIZED
                )

            jwt = get_jwt()
            if 'user_id' not in jwt:
                return make_response(
                    jsonify(error_mode='IDENTITY_MISSING',
                            message='User id not found in decrypted content'),
                    HTTPStatus.BAD_REQUEST)

            kwargs['user_id'] = jwt['user_id']
            return fn(*args, **kwargs)  # pragma: no cover

        return decorator

    return wrapper
