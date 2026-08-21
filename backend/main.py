"""FastAPI 入口：自动建表 + 挂载路由 + 静态前端（Docker 部署时）。"""
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db import engine, init_db
from routers import tasks, share

logger = logging.getLogger("diff_lab")
logger.setLevel(os.environ.get("DIFF_LAB_LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Diff.lab",
    description="两列数据差异对比工具",
    version="0.1.0",
    lifespan=lifespan,
)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _error_response(
    status_code: int,
    code: str,
    message: str,
    request: Request,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "detail": message,
            "error": {"code": code, "message": message, "request_id": _request_id(request)},
        },
    )


@app.middleware("http")
async def request_context_and_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
        response = _error_response(500, "INTERNAL_ERROR", "Internal server error", request)

    duration_ms = (time.perf_counter() - started_at) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return _error_response(exc.status_code, "HTTP_ERROR", message, request, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info("request_validation_failed request_id=%s errors=%s", _request_id(request), exc.errors())
    return _error_response(422, "VALIDATION_ERROR", "Invalid request", request)

# CORS：开发期允许 Vue dev server 跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由（API 在前）
app.include_router(tasks.router)
app.include_router(share.router)


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("healthcheck_database_failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "database": "ok"}


@app.get("/api-info")
def api_info():
    """仅当没有静态文件时返回（开发模式）。"""
    return {"name": "Diff.lab API", "version": "0.1.0", "docs": "/docs"}


# Docker 部署时挂载前端静态文件（SPA 路由兜底交给前端）
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    # 1. 挂载 /assets 子目录（直接返回静态资源）
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # 2. 根路径显式返回 index.html。Starlette 的 path 参数不会匹配空路径，
    #    因此仅依赖下面的通配路由会导致 Docker 部署后访问 / 返回 404。
    @app.get("/", include_in_schema=False)
    def spa_root():
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"error": "frontend not built"}

    # 3. SPA 路由兜底：所有非 /api 的 GET 请求都返回 index.html 或对应静态文件
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        # 先尝试返回静态文件（如 favicon.svg）
        f = STATIC_DIR / full_path
        if f.is_file():
            return FileResponse(f)
        # 否则返回 index.html（SPA 路由兜底）
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"error": "frontend not built"}
