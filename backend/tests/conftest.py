import importlib
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """每个 API 测试使用独立 SQLite 文件，避免污染本地开发数据。"""
    monkeypatch.setenv("DIFF_LAB_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("DIFF_LAB_ADMIN_TOKEN", "test-admin-token")
    for module_name in ("main", "db", "models", "routers", "routers.tasks", "routers.share"):
        sys.modules.pop(module_name, None)

    app_module = importlib.import_module("main")
    with TestClient(app_module.app) as test_client:
        yield test_client

    for module_name in ("main", "db", "models", "routers", "routers.tasks", "routers.share"):
        sys.modules.pop(module_name, None)
