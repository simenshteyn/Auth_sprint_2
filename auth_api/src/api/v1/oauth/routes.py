from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from flask import Blueprint, jsonify, make_response

from core.containers import Container
from core.utils import ServiceException
from models.social_accounts import SocialSignupResult
from services.oauth_login import OauthService
from services.user import UserService

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


@oauth.route('/login/callback/<provider>')
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


@oauth.route('/signup/<provider>')
@inject
def oauth_signup_authorize(
        provider: str,
        oauth_service: OauthService = Provide[Container.oauth_service]):
    return oauth_service.authorize_signup(provider)


@oauth.route('/signup/callback/<provider>')
@inject
def oauth_signup_callback(
        provider: str,
        oauth_service: OauthService = Provide[Container.oauth_service],
        user_service: UserService = Provide[Container.user_service]):
    try:
        # access_token, refresh_token = oauth_service.signup(provider,
        #                                                    user_service)
        result = oauth_service.signup(provider, user_service)
        if isinstance(result, SocialSignupResult):
            return make_response(
                jsonify(access_token=result.access_token,
                        refresh_token=result.refresh_token,
                        username=result.username,
                        password=result.password,
                        email=result.email),
                HTTPStatus.OK)
        access_token, refresh_token = result
    except ServiceException as err:
        return make_response(jsonify(err), HTTPStatus.BAD_REQUEST)
    return make_response(
        jsonify(access_token=access_token, refresh_token=refresh_token),
        HTTPStatus.OK)
