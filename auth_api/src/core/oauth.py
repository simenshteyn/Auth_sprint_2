import json

from flask import current_app, url_for, redirect, request
from rauth import OAuth2Service

from core.settings import config


class OAuthBase(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class OAuthSignIn(OAuthBase):
    def get_callback_url(self):
        return url_for('api.v1.oauth.oauth_callback',
                       provider=self.provider_name,
                       _external=True)


class OAuthSignUp(OAuthBase):
    def get_callback_url(self):
        return url_for('api.v1.oauth.oauth_signup_callback',
                       provider=self.provider_name,
                       _external=True)


class VkSignIn(OAuthSignIn):
    def __init__(self):
        super(VkSignIn, self).__init__('vk')
        self.service = OAuth2Service(
            name='vk',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://oauth.vk.com/authorize',
            access_token_url='https://oauth.vk.com/access_token',
            base_url='https://api.vk.com/method/'
        )

    def authorize(self):
        result = redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            v=config.vk_api_version,
            redirect_uri=self.get_callback_url())
        )
        return result

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        try:
            oauth_session = self.service.get_auth_session(
                method='GET', params={
                    'client_id': self.consumer_id,
                    'client_secret': self.consumer_secret,
                    'redirect_uri': self.get_callback_url(),
                    'code': request.args['code']
                }, decoder=decode_json)
            response = oauth_session.access_token_response.json()
        except Exception:
            return None, None, None
        return (str(response.get('user_id')),
                self.provider_name,
                response.get('email'))


class VkSignUp(OAuthSignUp):
    def __init__(self):
        super(VkSignUp, self).__init__('vk')
        self.service = OAuth2Service(
            name='vk',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://oauth.vk.com/authorize',
            access_token_url='https://oauth.vk.com/access_token',
            base_url='https://api.vk.com/method/'
        )

    def authorize(self):
        result = redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            v=config.vk_api_version,
            redirect_uri=self.get_callback_url())
        )
        return result

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None
        try:
            oauth_session = self.service.get_auth_session(
                method='GET', params={
                    'client_id': self.consumer_id,
                    'client_secret': self.consumer_secret,
                    'redirect_uri': self.get_callback_url(),
                    'code': request.args['code']
                }, decoder=decode_json)
            response = oauth_session.access_token_response.json()
        except Exception:
            return None, None, None
        return (str(response.get('user_id')),
                self.provider_name,
                response.get('email'))
