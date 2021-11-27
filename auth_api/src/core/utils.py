import sys
from dataclasses import dataclass
from functools import wraps
from http import HTTPStatus

import opentracing
from core.tracer import tracer
from db.redis_client import redis
from flask import jsonify, make_response, request
from flask_jwt_extended import get_jwt
from pydantic import ValidationError


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


def rate_limit(max_rate):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Only imposing the limits on user-identified requests
            if 'user_id' not in kwargs:
                return fn(*args, **kwargs)  # pragma: no cover

            key = f"buffer:{kwargs['user_id']}"
            buffer_size = redis.incr(key, 1)
            if buffer_size > 10:
                redis.decr(key)
                return make_response(
                    jsonify(error_code='TOO_MANY_REQUESTS',
                            message='API rate limit exceeded'),
                    HTTPStatus.TOO_MANY_REQUESTS
                )
            result = fn(*args, **kwargs)  # pragma: no cover
            redis.decr(key)
            return result

        return decorator

    return wrapper


def trace(func):
    """ Decorator to use with FlaskTracer on any function in route. """

    @wraps(func)
    def wrapper(*args, **kwargs):
        parent_span = tracer.get_flask_tracer().get_span()
        if request:
            request_id = request.headers.get('X-Request-Id')
            if request_id:
                parent_span.set_tag('http.request_id', request_id)
        with opentracing.tracer.start_span(operation_name=func.__name__,
                                           child_of=parent_span):
            return func(*args, **kwargs)

    return wrapper


def get_auth_headers(token: str):
    return {'Authorization': 'Bearer ' + token}
