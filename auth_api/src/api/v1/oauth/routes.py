from dependency_injector.wiring import inject, Provide
from flask import Blueprint, jsonify

from core.containers import Container

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
    result = oauth_service.get_info(provider)
    return jsonify(result)
