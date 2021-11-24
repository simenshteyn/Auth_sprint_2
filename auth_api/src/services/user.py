from typing import Union

from flask import Request, Response
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash, generate_password_hash

from core.settings import config
from core.utils import ServiceException
from db.pg import db
from db.redis_client import redis
from models.auth_event import AuthEvent
from models.token import Token
from models.user import LoginRequest, ModifyRequest, SignupRequest, User
from services.base import BaseService


def generate_tokens(user: User):
    """ Create new access and refresh tokens for the user"""
    user_data = {'user_id': user.user_id, }
    access_token = create_access_token(
        identity=user.user_id, additional_claims=user_data
    )
    refresh_token = create_refresh_token(
        identity=user.user_id, additional_claims=user_data
    )
    return access_token, refresh_token


def authenticate(access_token) -> None:
    """Check that access token is fresh"""
    if not redis.get(access_token) == b'':
        raise ServiceException(error_code='ACCESS_TOKEN_EXPIRED',
                               message='Access token has expired')


class UserService(BaseService):
    def create_user(self,
                    username: str,
                    password: str,
                    email: str):
        existing_user: User = User.query.filter(
            (User.user_login == username) | (User.user_email == email)
        ).first()

        if existing_user:
            if existing_user.user_login == username:
                error_code = self.LOGIN_EXISTS.code
                message = self.LOGIN_EXISTS.message
            else:
                error_code = self.EMAIL_EXISTS.code
                message = self.EMAIL_EXISTS.message
            raise ServiceException(error_code=error_code, message=message)

        password_hash = generate_password_hash(password)

        user = User(user_login=username,
                    user_password=password_hash,
                    user_email=email)
        db.session.add(user)
        db.session.commit()
        return user

    def register_user(self,
                      username: str,
                      password: str,
                      email: str,
                      user_info: dict):
        """ Check that a new user with these credentials can be added,
        if so, create the user and return its access and refresh tokens,
        otherwise, throw an exception telling what happened """
        user = self.create_user(username, password, email)
        access_token, refresh_token = generate_tokens(user)
        self.commit_authentication(user,
                                   'signup',
                                   access_token,
                                   refresh_token,
                                   user_info)

        return access_token, refresh_token

    def login(self, username: str, password: str, user_info: dict) \
            -> tuple[str, str]:

        user: User = User.query.filter(
            User.user_login == username
        ).first()

        if not user:
            raise ServiceException(error_code=self.USER_NOT_FOUND.code,
                                   message=self.USER_NOT_FOUND.message)

        if not check_password_hash(user.user_password, password):
            raise ServiceException(error_code=self.WRONG_PASSWORD.code,
                                   message=self.WRONG_PASSWORD.message)

        access_token, refresh_token = generate_tokens(user)
        self.commit_authentication(user=user,
                                   event_type='login',
                                   access_token=access_token,
                                   refresh_token=refresh_token,
                                   user_info=user_info)

        return access_token, refresh_token

    def refresh(self, user_id: str, refresh_token: str) -> tuple[str, str]:
        user: User = User.query.get(user_id)

        if not user:
            raise ServiceException(error_code=self.USER_NOT_FOUND.code,
                                   message=self.USER_NOT_FOUND.message)

        # Find refresh cookie to make sure its
        # the *last* emitted one.
        # The Refresh request will disqualify any previously emitted (stolen)
        # refresh cookies
        current_refresh_token = Token.query.filter(
            Token.token_value == refresh_token).first()
        if not current_refresh_token:
            raise ServiceException(error_code=self.INVALID_REFRESH_TOKEN.code,
                                   message=self.INVALID_REFRESH_TOKEN.message)

        access_token, refresh_token = generate_tokens(user)
        db.session.delete(current_refresh_token)
        db.session.commit()

        self.commit_authentication(user=user,
                                   event_type='refresh',
                                   access_token=access_token,
                                   refresh_token=refresh_token)

        return access_token, refresh_token

    def logout(self, user_id: str, access_token: str, refresh_token: str):
        user: User = User.query.get(user_id)

        authenticate(access_token)

        if not user:
            raise ServiceException(error_code=self.USER_NOT_FOUND.code,
                                   message=self.USER_NOT_FOUND.message)

        current_refresh_token = Token.query.filter(
            Token.token_value == refresh_token).first()
        if not current_refresh_token:
            raise ServiceException(error_code=self.INVALID_REFRESH_TOKEN.code,
                                   message=self.INVALID_REFRESH_TOKEN.message)
        # Delete the access token
        db.session.delete(current_refresh_token)
        db.session.commit()

        # Delete the refresh token
        redis.delete(access_token)

        return access_token, refresh_token

    def modify(self, user_id, new_username: str, new_password: str):
        """change user's username and password"""
        user: User = User.query.get(user_id)

        if not user:
            raise ServiceException(error_code=self.USER_NOT_FOUND.code,
                                   message=self.USER_NOT_FOUND.message)

        if not new_username == user.user_login:
            # make sure there is no other user with the target username
            existing_user = User.query.filter(
                (User.user_login == new_username)
            ).first()

            if existing_user:
                raise ServiceException(error_code=self.LOGIN_EXISTS.code,
                                       message=self.LOGIN_EXISTS.message)

            user.user_login = new_username

        if not new_password == user.user_password:
            user.user_password = new_password

        if db.session.is_modified(user):
            db.session.commit()

    def get_auth_history(self, user_id):
        history: list[AuthEvent] = AuthEvent.query.filter(
            (AuthEvent.auth_event_owner_id == user_id)
        ).all()

        result = []
        for event in history:
            result.append({'uuid': event.auth_event_id,
                           'time': event.auth_event_time,
                           'fingerprint': event.auth_event_fingerprint})
        return result

    # TODO: see if this can be reused on login or disassemble it
    @staticmethod
    def commit_authentication(user: User,
                              event_type: str,
                              access_token: str,
                              refresh_token: str,
                              user_info: dict = None):
        """ Finalize successful authentication saving the details."""
        token = Token(token_owner_id=user.user_id, token_value=refresh_token)
        db.session.add(token)

        if event_type == 'login':
            auth_event = AuthEvent(auth_event_owner_id=user.user_id,
                                   auth_event_type=event_type,
                                   auth_event_fingerprint=str(user_info))
            db.session.add(auth_event)

        db.session.commit()
        redis.set(name=access_token,
                  value='',
                  ex=config.access_token_expiration)

    def validate_signup(
            self, request: Request) -> Union[SignupRequest, Response]:
        return self._validate(request, SignupRequest)

    def validate_login(
            self, request: Request) -> Union[LoginRequest, Response]:
        return self._validate(request, LoginRequest)

    def validate_modify(
            self, request: Request) -> Union[ModifyRequest, Response]:
        return self._validate(request, ModifyRequest)
