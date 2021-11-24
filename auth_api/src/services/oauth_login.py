from core.oauth import OAuthSignIn


class OauthService:
    def __init__(self):
        pass

    def authorize(self, provider: str):
        oauth = OAuthSignIn.get_provider(provider)
        return oauth.authorize()

    def get_info(self, provider):
        oauth = OAuthSignIn.get_provider(provider)
        social_id, social_name, email = oauth.callback()
        result = {'social_id': social_id,
                  'social_name': social_name,
                  'email': email}
        return result
