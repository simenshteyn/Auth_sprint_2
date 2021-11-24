from http import HTTPStatus

import pytest

from tests.functional.settings import config
from tests.functional.utils.db_utils import get_auth_headers, remove_user, \
    get_user_uuid
from tests.functional.utils.extract import (extract_perm_check,
                                            extract_permission,
                                            extract_permissions, extract_role,
                                            extract_roles, extract_tokens)


@pytest.mark.asyncio
async def test_role_endpoint_crud(make_post_request, make_get_request,
                                  make_patch_request, make_delete_request,
                                  get_superuser_token):
    """Test roles CRUD cycle: creation, read, update and deletion. """
    access_token = get_superuser_token

    # Create new role
    response = await make_post_request('role/',
                                       json={'role_name': 'test_role'},
                                       headers=get_auth_headers(access_token))
    role = await extract_role(response)
    role_uuid = role.uuid
    assert response.status == HTTPStatus.OK
    assert role.role_name == 'test_role'

    # Get list of roles with created one
    response = await make_get_request('role/',
                                      headers=get_auth_headers(access_token))
    roles = await extract_roles(response)
    assert response.status == HTTPStatus.OK
    assert len(roles) == 2

    # Rename role by UUID
    response = await make_patch_request(f'role/{role_uuid}',
                                        json={'role_name': 'test_role_2'},
                                        headers=get_auth_headers(access_token))
    role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert role.role_name == 'test_role_2'

    # Remove role by UUID
    response = await make_delete_request(
        f'role/{role_uuid}',
        headers=get_auth_headers(access_token)
    )
    role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert role.role_name == 'test_role_2'
    assert role.uuid == role_uuid

    # Get list of roles with superadmin role only
    response = await make_get_request('role/',
                                      headers=get_auth_headers(access_token))
    roles = await extract_roles(response)
    assert response.status == HTTPStatus.OK
    assert len(roles) == 1
    assert roles[0].role_name == config.service_admin_role


@pytest.mark.asyncio
async def test_role_permissions_assigment(make_post_request, make_get_request,
                                          make_delete_request,
                                          get_superuser_token):
    """Test permissions CRUD assigment: create, assign and remove process. """
    access_token = get_superuser_token

    # Create new role and save it's uuid
    response = await make_post_request('role/',
                                       json={'role_name': 'testing_r'},
                                       headers=get_auth_headers(access_token))
    created_role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert created_role.role_name == 'testing_r'
    role_uuid = created_role.uuid

    # Create new permission and save it's uuid
    response = await make_post_request('permission/',
                                       json={'permission_name': 'testing_p'},
                                       headers=get_auth_headers(access_token))
    created_permission = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert created_permission.permission_name == 'testing_p'
    perm_uuid = created_permission.uuid

    # Assign created permission to created role
    response = await make_post_request(f'role/{role_uuid}/permissions',
                                       json={'permission_uuid': perm_uuid},
                                       headers=get_auth_headers(access_token))
    assigned_permission = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert assigned_permission.uuid == perm_uuid
    assert assigned_permission.permission_name == 'testing_p'

    # Get permissions for created role
    response = await make_get_request(f'role/{role_uuid}/permissions',
                                      headers=get_auth_headers(access_token))
    permissions_list = await extract_permissions(response)
    assert response.status == HTTPStatus.OK
    assert len(permissions_list) == 1
    assert permissions_list[0].permission_name == 'testing_p'
    assert permissions_list[0].uuid == perm_uuid

    # Remove created permission from Role
    response = await make_delete_request(
        f'role/{role_uuid}/permissions/{perm_uuid}',
        headers=get_auth_headers(access_token))
    removed_permission = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert removed_permission.permission_name == 'testing_p'
    assert removed_permission.uuid == perm_uuid

    # Check removed permission is excluded from role
    response = await make_get_request(f'role/{role_uuid}/permissions',
                                      headers=get_auth_headers(access_token))
    permissions_list = await extract_permissions(response)
    assert response.status == HTTPStatus.OK
    assert len(permissions_list) == 0

    # Remove created role
    response = await make_delete_request(
        f'role/{role_uuid}', headers=get_auth_headers(access_token))
    removed_role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert removed_role.role_name == 'testing_r'
    assert removed_role.uuid == role_uuid

    # Remove created permission
    response = await make_delete_request(
        f'permission/{perm_uuid}', headers=get_auth_headers(access_token))
    perm = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert perm.uuid == perm_uuid

    # Get list of roles with superadmin role only
    response = await make_get_request('role/',
                                      headers=get_auth_headers(access_token))
    roles = await extract_roles(response)
    assert response.status == HTTPStatus.OK
    assert len(roles) == 1
    assert roles[0].role_name == config.service_admin_role


@pytest.mark.asyncio
async def test_user_role_assigment(make_post_request, make_get_request,
                                   make_delete_request, pg_curs,
                                   get_superuser_token, redis_client):
    """Test full cycle of Role assigment to User: add, get, check, remove. """
    access_token = get_superuser_token

    # Create new user and save it's uuid and tokens
    response = await make_post_request('user/signup',
                                       json={'username': 'some_test_user',
                                             'password': 'some_password',
                                             'email': 'some@email.com'},
                                       headers=get_auth_headers(access_token))
    tokens = await extract_tokens(response)
    assert response.status == HTTPStatus.OK
    assert len(tokens.access_token) > 1
    assert len(tokens.refresh_token) > 1
    user_uuid = get_user_uuid(pg_curs, username='some_test_user')

    # Create new role and save it's uuid
    response = await make_post_request('role/',
                                       json={'role_name': 'testing_role'},
                                       headers=get_auth_headers(access_token))
    created_role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert created_role.role_name == 'testing_role'
    role_uuid = created_role.uuid

    # Create new permission and save it's uuid
    response = await make_post_request('permission/',
                                       json={'permission_name': 'testing_per'},
                                       headers=get_auth_headers(access_token))
    created_permission = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert created_permission.permission_name == 'testing_per'
    perm_uuid = created_permission.uuid

    # Assign created permission to created role
    response = await make_post_request(f'role/{role_uuid}/permissions',
                                       json={'permission_uuid': perm_uuid},
                                       headers=get_auth_headers(access_token))
    assigned_permission = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert assigned_permission.uuid == perm_uuid
    assert assigned_permission.permission_name == 'testing_per'

    # Check cache for that user and permission is empty
    cache = await redis_client.get(f'{user_uuid}:{perm_uuid}')
    assert not cache

    # Check if created User don't have permission by uuid till it assigned
    response = await make_get_request(
        f'user/{user_uuid}/permissions/{perm_uuid}',
        headers=get_auth_headers(access_token)
    )
    perm_check = await extract_perm_check(response)
    assert response.status == HTTPStatus.OK
    assert not perm_check.is_permitted

    # Check cache for that user and permission is false
    cache = await redis_client.get(f'{user_uuid}:{perm_uuid}')
    assert cache == 'denied'

    # Assign created role to created user
    response = await make_post_request(f'user/{user_uuid}/roles',
                                       json={'role_uuid': role_uuid},
                                       headers=get_auth_headers(access_token))
    assigned_role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert assigned_role.role_name == 'testing_role'
    assert assigned_role.uuid == role_uuid

    # Get assigned roles for created user
    response = await make_get_request(f'user/{user_uuid}/roles',
                                      headers=get_auth_headers(access_token))
    assigned_roles = await extract_roles(response)
    assert response.status == HTTPStatus.OK
    assert len(assigned_roles) == 1
    assert assigned_roles[0].role_name == 'testing_role'

    # Get permissions list for created user
    response = await make_get_request(f'user/{user_uuid}/permissions',
                                      headers=get_auth_headers(access_token))
    user_perms = await extract_permissions(response)
    assert response.status == HTTPStatus.OK
    assert len(user_perms) == 1
    assert user_perms[0].permission_name == 'testing_per'

    # Check if created User have permission by uuid
    response = await make_get_request(
        f'user/{user_uuid}/permissions/{perm_uuid}',
        headers=get_auth_headers(access_token)
    )
    perm_check = await extract_perm_check(response)
    assert response.status == HTTPStatus.OK
    assert perm_check.is_permitted

    # Check user permission is cached
    cache = await redis_client.get(f'{user_uuid}:{perm_uuid}')
    assert cache == 'accepted'

    # Remove assigned role from created user
    response = await make_delete_request(
        f'user/{user_uuid}/roles/{role_uuid}',
        headers=get_auth_headers(access_token)
    )
    removed_role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert removed_role.role_name == 'testing_role'
    assert removed_role.uuid == role_uuid

    # Check if created User lost permission by uuid after role removing
    response = await make_get_request(
        f'user/{user_uuid}/permissions/{perm_uuid}',
        headers=get_auth_headers(access_token)
    )
    perm_check = await extract_perm_check(response)
    assert response.status == HTTPStatus.OK
    assert not perm_check.is_permitted

    # Check role is excluded from users role list
    response = await make_get_request(
        f'user/{user_uuid}/roles',
        headers=get_auth_headers(access_token)
    )
    user_roles = await extract_roles(response)
    assert response.status == HTTPStatus.OK
    assert len(user_roles) == 0

    # Remove created permission
    response = await make_delete_request(
        f'permission/{perm_uuid}',
        headers=get_auth_headers(access_token)
    )
    perm = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert perm.uuid == perm_uuid

    # Remove created role
    response = await make_delete_request(
        f'role/{role_uuid}',
        headers=get_auth_headers(access_token)
    )
    removed_role = await extract_role(response)
    assert response.status == HTTPStatus.OK
    assert removed_role.role_name == 'testing_role'
    assert removed_role.uuid == role_uuid

    # Remove created user
    remove_user(pg_curs, user_uuid)
