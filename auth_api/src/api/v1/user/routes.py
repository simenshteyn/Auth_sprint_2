from http import HTTPStatus
from time import sleep

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, Response, jsonify, make_response, request
from flask_jwt_extended import get_jwt, jwt_required

from core.containers import Container
from core.settings import config
from core.utils import ServiceException, authenticate, rate_limit
from models.permission import Permission
from models.role import Role
from services.user import UserService
from services.user_perms import UserPermsService
from services.user_role import UserRoleService

user = Blueprint('user', __name__, url_prefix='/user')


@user.route('/signup', methods=["POST"])
@inject
def signup(user_service: UserService = Provide[Container.user_service]):
    """ Creates a new user and returns it's access and refresh tokens """
    signup_request = user_service.validate_signup(request)
    if isinstance(signup_request, Response):
        return signup_request

    user_info = {'user-agent': request.headers.get('User-Agent')}

    try:
        access_token, refresh_token = user_service.register_user(
            signup_request.username,
            signup_request.password,
            signup_request.email,
            user_info)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)

    return make_response(
        jsonify(access_token=access_token, refresh_token=refresh_token),
        HTTPStatus.OK)


@user.route('/auth', methods=["POST"])
@inject
def login(user_service: UserService = Provide[Container.user_service]):
    """ Log user in using username and password.
        Return a newly generated pair of tokens.
     """
    login_request = user_service.validate_login(request)
    if isinstance(login_request, Response):
        return login_request

    user_info = {'user-agent': request.headers.get('User-Agent')}

    try:
        access_token, refresh_token = user_service.login(
            login_request.username,
            login_request.password,
            user_info)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)

    return make_response(
        jsonify(access_token=access_token, refresh_token=refresh_token),
        HTTPStatus.OK)


@user.route('/auth', methods=["PUT"])
@jwt_required(refresh=True)
@inject
def refresh(user_service: UserService = Provide[Container.user_service]):
    jwt = get_jwt()
    refresh_token = request.headers['Authorization'].split().pop(-1)

    if 'user_id' not in jwt:
        return make_response(
            jsonify(error_mode='IDENTITY_MISSING',
                    message="User id not found in decrypted content"),
            HTTPStatus.BAD_REQUEST)

    try:
        access_token, refresh_token = user_service.refresh(
            user_id=jwt['user_id'],
            refresh_token=refresh_token)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)

    return make_response(jsonify(access_token=access_token,
                                 refresh_token=refresh_token))


@user.route('/auth/logout', methods=["POST"])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def logout(user_id: str,
           user_service: UserService = Provide[Container.user_service]):
    access_token = request.headers['Authorization'].split().pop(-1)
    request_json = request.json
    refresh_token = request_json['refresh_token']

    try:
        access_token, refresh_token = user_service.logout(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token
        )
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)

    return make_response(jsonify(access_token=access_token,
                                 refresh_token=refresh_token))


@user.route('/auth', methods=["PATCH"])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def modify(
        user_id: str,
        user_service: UserService = Provide[Container.user_service]):
    modify_request = user_service.validate_modify(request)
    if isinstance(modify, Response):
        return modify_request

    try:
        user_service.modify(user_id, modify_request.username,
                            modify_request.password)
    except ServiceException as err:
        return make_response(jsonify(err), 400)

    return make_response({}, HTTPStatus.ACCEPTED)


@user.route('/auth', methods=["GET"])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
@inject
def auth_history(user_id: str,
                 user_service: UserService = Provide[Container.user_service]
                 ):
    try:
        history = user_service.get_auth_history(user_id)
    except ServiceException as err:
        return make_response(jsonify(err), 400)

    return make_response(jsonify(history), HTTPStatus.OK)


@user.route('/<uuid:user_uuid>/roles', methods=['POST'])
@jwt_required()
@authenticate()
@inject
def assign_user_role(
        user_id: str,
        user_uuid: str,
        user_role_service: UserRoleService = Provide[
            Container.user_role_service]):
    set_request = user_role_service.validate_assignment(request)
    if isinstance(set_request, Response):
        return set_request
    try:
        user_role_service.check_superuser_authorization(user_id)
        new_role: Role = user_role_service.assign_user_role(
            user_id=user_uuid,
            role_id=set_request.role_uuid)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)
    return make_response(
        jsonify(uuid=new_role.role_id,
                role_name=new_role.role_name),
        HTTPStatus.OK
    )


@user.route('/<uuid:user_uuid>/roles', methods=['GET'])
@jwt_required()
@authenticate()
@inject
def get_user_roles_list(
        user_id: str,
        user_uuid: str,
        user_role_service: UserRoleService = Provide[
            Container.user_role_service]):
    try:
        user_role_service.check_superuser_authorization(user_id)
        roles_list = user_role_service.get_user_roles_list(user_uuid)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)
    result = [{'uuid': role.role_id,
               'role_name': role.role_name} for role in roles_list]
    return jsonify(result)


@user.route('/<uuid:user_uuid>/roles/<uuid:role_uuid>', methods=['DELETE'])
@jwt_required()
@authenticate()
@inject
def remove_role_from_user(
        user_id: str,
        user_uuid: str,
        role_uuid: str,
        user_role_service: UserRoleService = Provide[
            Container.user_role_service]):
    try:
        user_role_service.check_superuser_authorization(user_id)
        role = user_role_service.remove_role_from_user(user_id=user_uuid,
                                                       role_id=role_uuid)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)
    return make_response(
        jsonify(uuid=role.role_id, role_name=role.role_name), HTTPStatus.OK
    )


@user.route('/<uuid:user_uuid>/permissions', methods=['GET'])
@jwt_required()
@authenticate()
@inject
def get_user_perms_list(
        user_id: str,
        user_uuid: str,
        user_perm_service: UserPermsService = Provide[
            Container.user_perm_service]):
    try:
        user_perm_service.check_superuser_authorization(user_id)
        perms_list: list[Permission] = user_perm_service.get_user_perms_list(
            user_uuid)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)
    result = [{'uuid': perm.permission_id,
               'permission_name': perm.permission_name} for perm in perms_list]
    return jsonify(result)


@user.route('/<uuid:user_uuid>/permissions/<uuid:perm_uuid>', methods=['GET'])
@inject
def check_user_perm(
        user_uuid: str,
        perm_uuid: str,
        user_perm_service: UserPermsService = Provide[
            Container.user_perm_service]):
    try:
        is_permitted = user_perm_service.check_user_perm(user_uuid, perm_uuid)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)
    return jsonify(user_uuid=user_uuid,
                   permission_uuid=perm_uuid,
                   is_permitted=is_permitted)


@user.route('/slow', methods=['GET'])
@jwt_required()
@authenticate()
@rate_limit(config.user_max_request_rate)
def slow(user_id: str):
    """Stub handle used for testing rate limiting
    in tests/functional/src/test_rate_limit.py """

    sleep(5)

    return make_response(
        jsonify(slept=1), HTTPStatus.OK
    )
