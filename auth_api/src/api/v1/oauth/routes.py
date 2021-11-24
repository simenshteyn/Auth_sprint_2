from http import HTTPStatus

from dependency_injector.wiring import inject, Provide
from flask import Blueprint, jsonify, make_response

from core.containers import Container
from core.utils import ServiceException

from services.oauth_login import OauthService

oauth = Blueprint('oauth', __name__, url_prefix='/oauth')


@oauth.route('/', methods=['GET'])
def oauth_index():
    return jsonify(result="Oauth index")


@oauth.route('/login/<provider>')
@inject
def oauth_authorize(
        provider: str,
        oauth_service: OauthService = Provide[Container.oauth_service]):
    return oauth_service.authorize(provider)


@oauth.route('/callback/<provider>')
@inject
def oauth_callback(
        provider: str,
        oauth_service: OauthService = Provide[Container.oauth_service]):
    try:
        access_token, refresh_token = oauth_service.login(provider)
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)

    return make_response(
        jsonify(access_token=access_token, refresh_token=refresh_token),
        HTTPStatus.OK)