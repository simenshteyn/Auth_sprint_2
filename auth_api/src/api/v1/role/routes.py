from http import HTTPStatus

from core.containers import Container
from core.settings import config
from core.utils import authenticate, rate_limit
from dependency_injector.wiring import Provide, inject
from flask import Blueprint, Response, jsonify, make_response, request
from flask_jwt_extended import jwt_required
from models.permission import Permission
from services.role import RoleService

role = Blueprint('role', __name__, url_prefix='/role')


@role.route('/', methods=['GET'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def get_roles(
        user_id: str,
        role_service: RoleService = Provide[Container.role_service]):
    role_service.check_superuser_authorization(user_id)
    role_list = role_service.get_roles_list()
    result = [{'uuid': role.role_id,
               'role_name': role.role_name} for role in role_list]
    return jsonify(result)


@role.route('/', methods=['POST'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def create_role(
        user_id: str,
        role_service: RoleService = Provide[Container.role_service]):
    create_request = role_service.validate_role_request(request)
    if isinstance(create_request, Response):
        return create_request
    role_service.check_superuser_authorization(user_id)
    new_role = role_service.create_role(create_request.role_name)
    return make_response(
        jsonify(uuid=new_role.role_id, role_name=new_role.role_name),
        HTTPStatus.OK
    )


@role.route('/<uuid:role_uuid>', methods=['PATCH'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def edit_role(user_id: str, role_uuid: str,
              role_service: RoleService = Provide[Container.role_service]):
    edit_request = role_service.validate_role_request(request)
    if isinstance(edit_request, Response):
        return edit_request
    role_service.check_superuser_authorization(user_id)
    edited_role = role_service.edit_role(
        role_id=role_uuid,
        role_name=edit_request.role_name
    )
    return make_response(
        jsonify(uuid=edited_role.role_id, role_name=edited_role.role_name),
        HTTPStatus.OK
    )


@role.route('/<uuid:role_uuid>', methods=['DELETE'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def delete_role(user_id: str, role_uuid: str,
                role_service: RoleService = Provide[Container.role_service]):
    role_service.check_superuser_authorization(user_id)
    deleted_role = role_service.delete_role(role_id=role_uuid)
    return make_response(
        jsonify(uuid=deleted_role.role_id, role_name=deleted_role.role_name),
        HTTPStatus.OK
    )


@role.route('/<uuid:role_uuid>/permissions', methods=['GET'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def get_role_permissions(
        user_id: str,
        role_uuid: str,
        role_service: RoleService = Provide[Container.role_service]):
    role_service.check_superuser_authorization(user_id)
    perm_list = role_service.get_role_permissions(role_uuid)
    result = [{'uuid': perm.permission_id,
               'permission_name': perm.permission_name} for perm in perm_list]
    return jsonify(result)


@role.route('/<uuid:role_uuid>/permissions', methods=['POST'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def set_role_permissions(
        user_id: str,
        role_uuid: str,
        role_service: RoleService = Provide[Container.role_service]):
    set_request = role_service.validate_perm_request(request)
    if isinstance(set_request, Response):
        return set_request
    role_service.check_superuser_authorization(user_id)
    new_perm: Permission = role_service.set_role_permissions(
        role_id=role_uuid,
        perm_id=set_request.permission_uuid)
    return make_response(
        jsonify(uuid=new_perm.permission_id,
                permission_name=new_perm.permission_name),
        HTTPStatus.OK
    )


@role.route('/<uuid:role_uuid>/permissions/<uuid:perm_uuid>',
            methods=['DELETE'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def remove_role_permissions(
        user_id: str,
        role_uuid: str,
        perm_uuid: str,
        role_service: RoleService = Provide[Container.role_service]):
    role_service.check_superuser_authorization(user_id)
    deleted_perm: Permission = role_service.remove_role_permissions(
        role_id=role_uuid,
        perm_id=perm_uuid
    )
    return make_response(
        jsonify(uuid=deleted_perm.permission_id,
                permission_name=deleted_perm.permission_name),
        HTTPStatus.OK
    )
