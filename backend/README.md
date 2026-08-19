# Diff.lab · 后端

两列数据差异对比工具的 FastAPI 后端。

## 🚀 快速启动

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

访问：
- API 文档：http://127.0.0.1:8001/docs
- 健康检查：http://127.0.0.1:8001/health

## 📡 API 接口

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/tasks` | 创建对比任务 |
| `GET` | `/api/tasks` | 列出所有任务 |
| `GET` | `/api/tasks/{id}` | 获取任务详情 |
| `DELETE` | `/api/tasks/{id}` | 删除任务 |
| `POST` | `/api/tasks/{id}/share` | 生成分享链接 |
| `GET` | `/api/share/{token}` | 通过分享链接访问 |
| `POST` | `/api/preview` | 实时预览（不存 DB） |

## 🧪 测试

安装开发依赖并运行自动化测试：

```bash
pip install -r requirements-dev.txt
pytest
```

```bash
# 健康检查
curl http://127.0.0.1:8001/health

# 创建任务
curl -X POST http://127.0.0.1:8001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "test",
    "mode": "find_diff",
    "column_a": "apple\nbanana",
    "column_b": "apple\ncherry",
    "options": {"ignore_case": false, "trim": false, "skip_empty": true}
  }'
```

## 🗄️ 数据库

- SQLite 单文件：`backend/diff_lab.db`（自动创建）
- 表结构：`diff_tasks` + `share_links`
- 数据保留期：90 天；启动时会清理过期记录，接口也不会返回或导出过期任务
- 单列限制：最多 1000 行、100,000 个字符
- Schema 由 Alembic 在应用启动时升级；迁移文件位于 `alembic/versions/`

## 📁 项目结构

```
backend/
├── main.py              # FastAPI 入口
├── db.py                # SQLite 连接
├── models.py            # ORM 模型 + Pydantic Schema
├── diff_engine.py       # 核心对比算法
├── routers/
│   ├── tasks.py         # 任务 CRUD
│   └── share.py         # 分享访问
├── requirements.txt
└── start.sh             # 一键启动脚本
```
