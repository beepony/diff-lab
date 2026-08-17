"""FastAPI 入口：自动建表 + 挂载路由 + 静态前端（Docker 部署时）。"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db import init_db
from routers import tasks, share

app = FastAPI(
    title="Diff.lab",
    description="两列数据差异对比工具",
    version="0.1.0",
)

# CORS：开发期允许 Vue dev server 跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时建表
@app.on_event("startup")
def startup():
    init_db()

# 路由（API 在前）
app.include_router(tasks.router)
app.include_router(share.router)


@app.get("/health")
def health():
    return {"status": "ok"}


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

    # 2. SPA 路由兜底：所有非 /api 的 GET 请求都返回 index.html 或对应静态文件
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