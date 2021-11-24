from dataclasses import dataclass

from multidict import CIMultiDictProxy
from pydantic import BaseModel, constr


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


class Role(BaseModel):
    uuid: str
    role_name: str


class Permission(BaseModel):
    uuid: str
    permission_name: str


class UserTokens(BaseModel):
    access_token: constr(min_length=1)
    refresh_token: constr(min_length=1)


class ServiceError(BaseModel):
    error_code: str
    message: str


class PermissionCheck(BaseModel):
    user_uuid: str
    permission_uuid: str
    is_permitted: bool
