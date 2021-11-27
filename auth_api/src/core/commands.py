import getpass

from core.containers import Container
from core.utils import ServiceException
from db.pg import db
from dependency_injector.wiring import Provide
from flask import Blueprint
from services.role import RoleService
from services.user import UserService
from services.user_role import UserRoleService

commands = Blueprint('manage', __name__)


# Running this command:
# docker exec --env FLASK_APP=main -it auth_app flask manage createsuperuser
#
# Note: this command doesn't use the API for security concerns:
# the API shouldn't be usable before creating a superuser,
# who will then grant permissions for the API usage.
#

def create_superuser(username: str, password: str, email: str,
                     role_service: RoleService = Provide[
                         Container.role_service],
                     user_service: UserService = Provide[
                         Container.user_service],
                     user_role_service: UserRoleService = Provide[
                         Container.user_role_service
                     ]
                     ):
    # Create the user
    user = user_service.create_user(username, password, email)

    superadmin_role = None
    superadmin_role_name = 'superadmin'
    roles = role_service.get_roles_list()

    # Find or create the role
    for role in roles:
        if role.role_name == superadmin_role_name:
            superadmin_role = role
            break

    if not superadmin_role:
        superadmin_role = role_service.create_role(superadmin_role_name)

    # add the role to the user
    user_role_service.assign_user_role(user.user_id,
                                       superadmin_role.role_id)
    db.session.commit()

    return user


@commands.cli.command('createsuperuser')
def create():
    username = input('Super user username: ')
    email = input('Super user email: ')

    while True:
        password = getpass.getpass('Password: ')
        password_again = getpass.getpass('Password again: ')
        if password_again == password:
            break
        print('Passwords do not match!')

    try:
        create_superuser(username, password, email)
    except ServiceException as err:
        print(f'ERROR: {err.message}')
        return

    print('Admin user created')
