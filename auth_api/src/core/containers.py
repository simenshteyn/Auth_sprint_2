from dependency_injector import containers, providers
from dependency_injector.ext import flask
from flask import Flask
from services.oauth_login import OauthService
from services.permission import PermissionService
from services.role import RoleService
from services.user import UserService
from services.user_perms import UserPermsService
from services.user_role import UserRoleService


class Container(containers.DeclarativeContainer):
    app = flask.Application(Flask, __name__)

    wiring_config = containers.WiringConfiguration(
        packages=[
            'api.v1.routes',
            'api.v1.user.routes',
            'api.v1.role.routes',
            'api.v1.permission.routes',
            'api.v1.oauth.routes',
            'core.commands'
        ],
    )

    user_service = providers.Factory(UserService)
    role_service = providers.Factory(RoleService)
    perm_service = providers.Factory(PermissionService)
    user_role_service = providers.Factory(UserRoleService)
    user_perm_service = providers.Factory(UserPermsService)
    oauth_service = providers.Factory(OauthService)
