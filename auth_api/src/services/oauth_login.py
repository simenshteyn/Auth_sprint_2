from core.oauth import OAuthSignIn
from core.utils import ServiceException
from db.pg import db
from models.social_accounts import SocialAccount
from models.user import User
from services.base import BaseService
from services.user import generate_tokens, UserService


class OauthService(BaseService):
    def __init__(self):
        pass

    def authorize(self, provider: str):
        oauth = OAuthSignIn.get_provider(provider)
        return oauth.authorize()

    def login(self, provider):
        """Method to login existing user with social account. """
        oauth = OAuthSignIn.get_provider(provider)
        social_id, social_name, email = oauth.callback()
        if not social_id:
            error_code = self.WRONG_CALLBACK.code
            message = self.WRONG_CALLBACK.message
            raise ServiceException(error_code=error_code, message=message)

        # Check if user has existing social account
        existing_social_account: SocialAccount = SocialAccount.query.filter(
            SocialAccount.social_id == social_id,
            SocialAccount.social_provider == social_name).first()
        if existing_social_account:
            user: User = User.query.get(existing_social_account.user_id)
            if not user:
                raise ServiceException(error_code=self.USER_NOT_FOUND.code,
                                       message=self.USER_NOT_FOUND.message)
            access_token, refresh_token = generate_tokens(user)
            UserService.commit_authentication(user=user,
                                              event_type='login',
                                              access_token=access_token,
                                              refresh_token=refresh_token,
                                              user_info={
                                                  'social_id': social_id,
                                                  'social_name': social_name,
                                                  'method': 'id'})
            return access_token, refresh_token

        # If there is no social account - try to find user by email and create
        user_with_email: User = User.query.filter(
            User.user_email == email).first()
        if user_with_email:
            new_social_account = SocialAccount(user_id=user_with_email.user_id,
                                               social_id=social_id,
                                               social_provider=social_name)
            db.session.add(new_social_account)
            db.session.commit()
            access_token, refresh_token = generate_tokens(user_with_email)
            UserService.commit_authentication(user=user_with_email,
                                              event_type='login',
                                              access_token=access_token,
                                              refresh_token=refresh_token,
                                              user_info={
                                                  'social_id': social_id,
                                                  'social_name': social_name,
                                                  'method': 'email'})

            return access_token, refresh_token

        # If we can't find user by social account and email from provider
        raise ServiceException(error_code=self.USER_NOT_FOUND.code,
                               message=self.USER_NOT_FOUND.message)
