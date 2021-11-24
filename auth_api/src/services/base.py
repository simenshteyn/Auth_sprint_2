from http import HTTPStatus
from typing import Union, Type
from collections import namedtuple

from flask import Request, Response, jsonify, make_response
from pydantic import BaseModel, ValidationError

from core.settings import config
from core.utils import make_service_exception, ServiceException
from models.role import Role
from models.roles_owners import RoleOwner
from models.user import User

Rcode = namedtuple('Rcode', 'code message')


class BaseService:
    USER_NOT_FOUND = Rcode('USER_NOT_FOUND', 'Unknown user UUID')
    ROLE_NOT_FOUND = Rcode('ROLE_NOT_FOUND', 'Role not found')
    NOT_PERMITTED = Rcode('NOT_PERMITTED', 'This requires another role')
    PERMISSION_NOT_FOUND = Rcode('PERMISSION_NOT_FOUND',
                                 'Permission with that UUID not found')
    PERMISSION_EXISTS = Rcode('PERMISSION_EXISTS',
                              'Permission with than name already exists')
    ROLE_EXISTS = Rcode('ROLE_EXISTS', 'Role with than name already exists')
    ROLE_PERMISSION_EXISTS = Rcode(
        'ROLE_PERMISSION_EXISTS',
        'Permission for Role with that UUID already exists')
    ROLE_PERMISSION_NOT_FOUND = Rcode(
        'ROLE_PERMISSION_NOT_FOUND',
        'Permission for Role with that UUID not found')
    NO_ROLE_OWNERSHIP = Rcode('NO_ROLE_OWNERSHIP',
                              'User has no ownership over this role')
    LOGIN_EXISTS = Rcode('LOGIN_EXISTS', 'This username is already taken')
    INVALID_REFRESH_TOKEN = Rcode('INVALID_REFRESH_TOKEN',
                                  'This refresh token is invalid')
    WRONG_PASSWORD = Rcode('WRONG_PASSWORD', 'The password is incorrect')
    EMAIL_EXISTS = Rcode('EMAIL_EXISTS', 'This email address is already used')
    ACCESS_TOKEN_EXPIRED = Rcode('ACCESS_TOKEN_EXPIRED',
                                 'Access token has expired')
    WRONG_CALLBACK = Rcode('WRONG_CALLBACK',
                           'Code or callback from social service is broken')

    def __init__(self):
        pass

    def _validate(
            self, request: Request, model: Type[BaseModel]
    ) -> Union[BaseModel, Response]:
        request_json = request.json
        try:
            create_request = model(**request_json)
        except ValidationError as err:
            service_exception = make_service_exception(err)
            return make_response(
                jsonify(service_exception),
                HTTPStatus.BAD_REQUEST
            )
        return create_request

    def check_superuser_authorization(
            self,
            user_id: str,
            role_name: str = config.service_admin_role) -> None:
        """Check if user has access to work with roles (superadmin role). """
        existing_user: User = User.query.get(user_id)
        if not existing_user:
            error_code = self.USER_NOT_FOUND.code
            message = self.USER_NOT_FOUND.message

            raise ServiceException(error_code=error_code, message=message)

        existing_superuser_role: Role = Role.query.filter(
            Role.role_name == role_name).first()
        if not existing_superuser_role:
            error_code = self.ROLE_NOT_FOUND.code
            message = self.ROLE_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_role_ownership: RoleOwner = RoleOwner.query.filter(
            RoleOwner.owner_id == user_id,
            RoleOwner.role_id == existing_superuser_role.role_id).first()
        if not existing_role_ownership:
            error_code = self.NOT_PERMITTED.code
            message = self.NOT_PERMITTED.message
            raise ServiceException(error_code=error_code, message=message)
