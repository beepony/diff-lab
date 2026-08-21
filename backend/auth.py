"""管理员认证与匿名用户身份校验。"""
import hashlib
import hmac
import os
import re

from fastapi import HTTPException, Request, status

USER_TOKEN_HEADER = "X-User-Token"
_USER_TOKEN_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def _provided_admin_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    bearer_token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
    return request.headers.get("X-Admin-Token") or bearer_token


def is_admin(request: Request) -> bool:
    """仅在服务端已配置令牌且请求令牌正确时返回 True。"""
    expected_token = os.environ.get("DIFF_LAB_ADMIN_TOKEN")
    provided_token = _provided_admin_token(request)
    return bool(expected_token and provided_token and hmac.compare_digest(provided_token, expected_token))


def require_admin(request: Request) -> None:
    """管理员操作始终受保护；未配置服务端令牌时禁用管理员接口。"""
    expected_token = os.environ.get("DIFF_LAB_ADMIN_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured",
        )

    if not is_admin(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


def user_token_hash(request: Request) -> str:
    """校验匿名用户令牌，并仅返回可安全持久化的 SHA-256 摘要。"""
    token = request.headers.get(USER_TOKEN_HEADER, "").strip()
    if not _USER_TOKEN_PATTERN.fullmatch(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identity required",
        )
    return hashlib.sha256(token.encode("ascii")).hexdigest()
