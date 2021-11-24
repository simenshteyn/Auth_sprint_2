from core.settings import config
from core.utils import ServiceException
from db.redis_client import redis
from models.permission import Permission
from models.role_permissions import RolePermission
from models.roles_owners import RoleOwner
from models.user import User
from services.base import BaseService


class UserPermsService(BaseService):
    def __init__(self):
        pass

    def get_user_perms_list(self, user_id: str) -> list[Permission]:
        """Get User list of Permissions. """
        existing_user: User = User.query.get(user_id)
        if not existing_user:
            error_code = self.USER_NOT_FOUND.code
            message = self.USER_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        existing_role_ownership = RoleOwner.query.filter(
            RoleOwner.owner_id == user_id).all()
        if not existing_role_ownership:
            return []

        role_ids = [ro.role_id for ro in existing_role_ownership]

        existing_rps = [
            RolePermission.query.filter(RolePermission.role_id == r_id).all()
            for
            r_id in role_ids]
        rp_list = [val for sublist in existing_rps for val in sublist]
        rp_list = list(set(rp_list))
        return [Permission.query.get(rp.permission_id) for rp in rp_list]

    def check_user_perm(self, user_id: str, perm_id: str) -> bool:
        """Check if User with given UUID have Permission with given UUID. """
        cache_value = redis.get(f'{user_id}:{perm_id}')
        if cache_value == 'denied':
            return False
        if cache_value == 'accepted':
            return True

        existing_permission: Permission = Permission.query.filter(
            Permission.permission_id == perm_id).first()
        if not existing_permission:
            error_code = self.PERMISSION_NOT_FOUND.code
            message = self.PERMISSION_NOT_FOUND.message
            raise ServiceException(error_code=error_code, message=message)

        user_perms: list[Permission] = self.get_user_perms_list(user_id)
        perm_ids: list[str] = [perm.permission_id for perm in user_perms]
        if perm_id in perm_ids:
            redis.set(
                name=f'{user_id}:{perm_id}',
                value='accepted',
                ex=config.cache_time)
            return True
        else:
            redis.set(
                name=f'{user_id}:{perm_id}',
                value='denied',
                ex=config.cache_time)
            return False
