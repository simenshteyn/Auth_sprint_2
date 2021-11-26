from typing import Union

from flask import Request, Response

from core.utils import ServiceException, trace
from db.pg import db
from models.permission import Permission, PermissionCreationRequest
from services.base import BaseService


class PermissionService(BaseService):
    def __init__(self):
        pass

    def get_permission_list(self) -> list[Permission]:
        return Permission.query.all()

    @trace
    def create_permission(self, permission_name: str) -> Permission:
        existing_permission: Permission = Permission.query.filter(
            Permission.permission_name == permission_name).first()

        if existing_permission:
            error_code = self.PERMISSION_EXISTS.code
            message = self.PERMISSION_EXISTS.message
            raise ServiceException(error_code=error_code, message=message)

        new_permission = Permission(permission_name=permission_name)
        db.session.add(new_permission)
        db.session.commit()
        return new_permission

    @trace
    def edit_permission(self, permission_id: str,
                        permission_name: str) -> Permission:
        existing_permission: Permission = Permission.query.filter(
            Permission.permission_id == permission_id).first()

        if not existing_permission:
            error_code = self.PERMISSION_NOT_FOUND.code
            message = self.PERMISSION_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_permission.permission_name = permission_name
        db.session.commit()
        return existing_permission

    @trace
    def delete_permission(self, permission_id: str) -> Permission:
        existing_permission: Permission = Permission.query.filter(
            Permission.permission_id == permission_id).first()

        if not existing_permission:
            error_code = self.PERMISSION_NOT_FOUND.code
            message = self.PERMISSION_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        db.session.delete(existing_permission)
        db.session.commit()
        return existing_permission

    def validate_request(
            self, request: Request
    ) -> Union[PermissionCreationRequest, Response]:
        return self._validate(request, PermissionCreationRequest)
