from typing import Union

from flask import Request, Response

from core.utils import ServiceException
from db.pg import db
from models.role import Role
from models.roles_owners import RoleOwner
from models.user import User, UserRoleAssignRequest
from services.base import BaseService


class UserRoleService(BaseService):
    def __init__(self):
        pass

    def get_user_roles_list(self, user_id: str) -> list[Role]:
        existing_user: User = User.query.get(user_id)
        if not existing_user:
            error_code = self.USER_NOT_FOUND.code
            message = self.USER_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_role_ownership = RoleOwner.query.filter(
            RoleOwner.owner_id == user_id).all()

        role_ids = [ro.role_id for ro in existing_role_ownership]
        roles = [Role.query.get(role_id) for role_id in role_ids]
        return roles

    def assign_user_role(self, user_id: str, role_id: str) -> Role:
        existing_user: User = User.query.get(user_id)
        if not existing_user:
            error_code = self.USER_NOT_FOUND.code
            message = self.USER_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_role: Role = Role.query.get(role_id)
        if not existing_role:
            error_code = self.ROLE_NOT_FOUND.code
            message = self.ROLE_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_role_ownership: RoleOwner = RoleOwner.query.filter(
            RoleOwner.role_id == role_id).filter(
            RoleOwner.owner_id == user_id).first()
        if existing_role_ownership:
            error_code = self.ROLE_EXISTS.code
            message = self.ROLE_EXISTS.message
            raise ServiceException(error_code=error_code, message=message)

        new_role_ownership = RoleOwner(owner_id=user_id, role_id=role_id)
        db.session.add(new_role_ownership)
        db.session.commit()

        new_role: Role = Role.query.get(role_id)
        return new_role

    def remove_role_from_user(self, user_id: str, role_id: str):
        existing_user: User = User.query.get(user_id)
        if not existing_user:
            error_code = self.USER_NOT_FOUND.code
            message = self.USER_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_role: Role = Role.query.get(role_id)
        if not existing_role:
            error_code = self.ROLE_NOT_FOUND.code
            message = self.ROLE_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_role_ownership: RoleOwner = RoleOwner.query.filter(
            RoleOwner.role_id == role_id).filter(
            RoleOwner.owner_id == user_id).first()
        if not existing_role_ownership:
            error_code = self.NO_ROLE_OWNERSHIP.code
            message = self.NO_ROLE_OWNERSHIP.message
            raise ServiceException(error_code=error_code, message=message)
        role = Role.query.get(role_id)
        db.session.delete(existing_role_ownership)
        db.session.commit()
        return role

    def validate_assignment(
            self, request: Request) -> Union[UserRoleAssignRequest, Response]:
        return self._validate(request, UserRoleAssignRequest)
