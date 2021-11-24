from http import HTTPStatus

import pytest

from tests.functional.utils.db_utils import get_auth_headers
from tests.functional.utils.extract import (extract_permission,
                                            extract_permissions)


@pytest.mark.asyncio
async def test_permission_endpoint_crud(make_post_request, make_get_request,
                                        make_patch_request,
                                        make_delete_request,
                                        get_superuser_token):
    """ Test CRUD cycle for Permission: create, read, update and delete."""
    access_token = get_superuser_token
    response = await make_post_request('permission/',
                                       json={'permission_name': 'test_perm'},
                                       headers=get_auth_headers(access_token))
    # Create permission
    perm = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert perm.permission_name == 'test_perm'
    perm_uuid = perm.uuid

    # Check permission is created
    response = await make_get_request('permission/',
                                      headers=get_auth_headers(access_token))
    perms = await extract_permissions(response)
    assert response.status == HTTPStatus.OK
    assert len(perms) > 0

    # Rename permission
    response = await make_patch_request(
        f'permission/{perm_uuid}',
        json={'permission_name': 'test_perm_2'},
        headers=get_auth_headers(access_token)
    )
    perm = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert perm.permission_name == 'test_perm_2'

    # Remove created permission by UUID
    response = await make_delete_request(
        f'permission/{perm_uuid}',
        headers=get_auth_headers(access_token)
    )
    perm = await extract_permission(response)
    assert response.status == HTTPStatus.OK
    assert perm.permission_name == 'test_perm_2'
    assert perm.uuid == perm_uuid
