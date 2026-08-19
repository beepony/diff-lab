"""可选的单管理员令牌认证，适用于内部部署。"""
import hmac
import os

from fastapi import HTTPException, Request, status


def require_admin(request: Request) -> None:
    """当配置了 DIFF_LAB_ADMIN_TOKEN 时，保护任务管理接口。"""
    expected_token = os.environ.get("DIFF_LAB_ADMIN_TOKEN")
    if not expected_token:
        return

    authorization = request.headers.get("Authorization", "")
    bearer_token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
    provided_token = request.headers.get("X-Admin-Token") or bearer_token
    if not provided_token or not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
