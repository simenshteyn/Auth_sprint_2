from flask import Blueprint, jsonify

from services.oauth import OAuthSignIn

oauth = Blueprint('oauth', __name__, url_prefix='/oauth')


@oauth.route('/', methods=['GET'])
def oauth_index():
    return jsonify(result="Oauth index")


@oauth.route('/login/<provider>')
def oauth_authorize(provider):
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@oauth.route('/callback/<provider>')
def oauth_callback(provider):
    oauth = OAuthSignIn.get_provider(provider)
    social_id, social_name, email = oauth.callback()
    result = {'social_id': social_id,
              'social_name': social_name,
              'email': email}
    return jsonify(result)
