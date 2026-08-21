# Diff.lab · 两列数据差异对比工具

> 像 VLOOKUP 一样好用，但更快、更直观、支持团队分享。
> Vue 3 + FastAPI + SQLite · 1000 行数据毫秒级对比 · 迁移可控 · 可选管理员保护 · 中英双语

![status](https://img.shields.io/badge/status-ready-success)
![license](https://img.shields.io/badge/license-MIT-blue)
![i18n](https://img.shields.io/badge/i18n-zh--CN%20%7C%20en--US-blue)
![docker](https://img.shields.io/badge/docker-ready-blue)
![tests](https://img.shields.io/badge/tests-15%20passed-success)

[English](#english) · [简体中文](#简体中文)

---

## 简体中文

### ✨ 功能

- **3 种对比模式** · 找差异 / VLOOKUP / 找交集
- **双列并排高亮** · 差异行染色 + 状态标签，视觉一眼可读
- **3 种匹配选项** · 忽略大小写 / 去空格 / 忽略空值
- **中英双语** · 自动检测浏览器语言，Hero 右上角一键切换，localStorage 持久化偏好
- **历史保存** · 自动持久化，90 天保留
- **分享链接** · 一键生成高熵 token，无需登录（默认 7 天、最长不超过任务 90 天保留期，可撤销）
- **安全导出** · CSV 流式下载、UTF-8 BOM 与公式注入防护
- **访问控制** · 匿名用户按浏览器隔离任务；管理员可管理全部任务；分享链接只读
- **可靠 SQLite** · WAL、外键、busy timeout、过期清理与健康检查
- **可演进数据结构** · Alembic 自动升级数据库 schema
- **可验证** · 后端 API / 迁移 / 安全边界自动化测试

### 🚀 快速启动

**方式 1 · Docker 单镜像（推荐）**

```bash
# 公网部署必须设置管理员令牌；普通用户身份由浏览器自动创建。
export DIFF_LAB_ADMIN_TOKEN="$(openssl rand -hex 32)"
docker-compose up -d --build
```

打开 http://localhost:8001

数据持久化在 Docker volume `diff-lab-data`（SQLite 文件）。

普通用户无需输入令牌。浏览器首次使用时会自动生成匿名身份，历史记录只返回该身份创建的任务。如需查看和管理全部任务，通过页面右下角“配置管理员令牌”输入服务端令牌。详细部署说明见 [docs/DEPLOY.md](docs/DEPLOY.md)。

**方式 2 · 本地开发（前后端分离）**

后端：
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

前端（新终端）：
```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173

运行后端测试：

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### 🌍 多语言支持

| 语言 | 代码 | 文件 |
|---|---|---|
| 简体中文 | `zh-CN` | `frontend/src/i18n/locales/zh-CN.json` |
| English | `en-US` | `frontend/src/i18n/locales/en-US.json` |

**自动检测顺序**：localStorage 偏好 → 浏览器语言 (`navigator.language`) → 默认中文。

**新增语言**：复制 `en-US.json` → 翻译 → 在 `src/i18n/index.js` 的 `SUPPORTED_LOCALES` 添加 → 在 `messages` 注册。

### 🏗️ 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3 + Vite 5 + vue-router 4 + axios + **vue-i18n 10** |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| 数据库 | SQLite（单文件，零运维） |
| 部署 | Docker 多阶段构建（前端静态嵌入 Python 镜像） |

### 📁 项目结构

```
diff-lab/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 入口 + 静态前端挂载 + SPA 兜底
│   ├── auth.py                 # 可选管理员 token 校验
│   ├── db.py                   # SQLite 连接、连接 PRAGMA 与迁移入口
│   ├── models.py               # ORM 模型 + Pydantic Schema
│   ├── diff_engine.py          # 核心对比算法（3 模式 + 标准化）
│   ├── alembic/                # 可版本化数据库迁移
│   ├── routers/
│   │   ├── tasks.py            # 受保护 CRUD + 预览 + 分享管理 + 导出
│   │   └── share.py            # 通过 token 访问
│   ├── tests/                  # 算法、API、迁移与安全测试
│   ├── requirements.txt
│   ├── start.sh
│   └── README.md
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue        # 首页：Hero + 三步引导 + 历史网格
│   │   │   ├── TaskDetail.vue  # 详情：双列并排 + 摘要 + 导出
│   │   │   └── ShareView.vue   # 分享视图（只读）
│   │   ├── components/
│   │   │   ├── LanguageSwitcher.vue  # 语言切换器
│   │   │   ├── AdminAccess.vue       # 会话级管理员令牌配置
│   │   │   ├── StepImport.vue        # 双列输入
│   │   │   ├── StepMode.vue          # 模式选择
│   │   │   └── StepResult.vue        # 结果表格
│   │   ├── i18n/
│   │   │   ├── index.js              # vue-i18n 配置 + 自动探测
│   │   │   └── locales/
│   │   │       ├── zh-CN.json        # 简体中文
│   │   │       └── en-US.json        # English
│   │   ├── router.js
│   │   ├── api.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── vite.config.js          # Vite 配置（含 @ alias + API proxy）
│   ├── index.html
│   └── package.json
├── docs/
│   └── DEPLOY.md               # Azure / 阿里云部署指南
├── Dockerfile                  # 多阶段构建
├── docker-compose.yml          # 一键启动
├── LICENSE                     # MIT
└── README.md
```

### 🔌 API 接口

| 方法 | 路径 | 用途 | 权限 |
|---|---|---|---|
| `POST` | `/api/tasks` | 创建对比任务 | 匿名用户身份 |
| `GET` | `/api/tasks` | 列出自己的历史；管理员列出全部 | 本人或管理员 |
| `GET` | `/api/tasks/{id}` | 获取任务详情 | 本人或管理员 |
| `DELETE` | `/api/tasks/{id}` | 删除任务 | 管理员 |
| `GET` | `/api/tasks/{id}/export` | 导出 CSV | 本人或管理员 |
| `GET` | `/api/tasks/{id}/share` | 查询当前分享链接 | 管理员 |
| `POST` | `/api/tasks/{id}/share` | 创建或获取有效分享链接 | 管理员 |
| `DELETE` | `/api/tasks/{id}/share` | 撤销当前分享链接 | 管理员 |
| `GET` | `/api/share/{token}` | 通过分享链接只读访问 | 分享令牌 |
| `POST` | `/api/preview` | 实时预览（不持久化） | 公开 |

完整 OpenAPI 文档：启动后访问 `/docs`

匿名用户身份使用 `X-User-Token`（64 位十六进制随机值），网页会自动生成并保存在 `localStorage`。管理员支持 `Authorization: Bearer <token>` 或 `X-Admin-Token: <token>`。

### 🔐 安全与运维

- **匿名用户身份** · 原始用户令牌仅保存在浏览器 `localStorage`，数据库只保存 SHA-256 摘要；清除浏览器数据或换设备后无法恢复原历史。
- **管理员 token** · 公网部署必须设置 `DIFF_LAB_ADMIN_TOKEN`；未配置时管理员接口返回 503。前端会即时验证令牌，并仅在 `sessionStorage` 保存。
- **旧任务** · 升级前创建、没有归属信息的任务仅管理员可见，不会自动分配给任何普通用户。
- **分享链接** · 默认为 7 天有效，可设为 1–90 天，且最长不超过任务的 90 天保留期；管理员可随时撤销。
- **输入与导出** · 每列最多 1000 行、100,000 字符；CSV 对公式前缀进行转义，避免在表格软件中执行用户输入。
- **请求可追踪** · API 返回 `X-Request-ID`，错误体也包含请求 ID；`/health` 会检查数据库连通性。
- **数据库** · 启动时自动执行 Alembic 迁移与过期数据清理；SQLite 启用 WAL、外键和 busy timeout。

### 🧪 验证

自动化测试覆盖核心算法、输入限制、CSV 防护、任务/分享过期、管理员授权、请求 ID 与迁移状态：

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

快速 API 测试：

```bash
curl -X POST http://localhost:8001/api/tasks \
  -H "Content-Type: application/json" \
  -H "X-User-Token: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" \
  -d '{
    "title": "测试",
    "mode": "find_diff",
    "column_a": "apple\nbanana",
    "column_b": "apple\ncherry",
    "options": {"ignore_case": false, "trim": false, "skip_empty": true}
  }'
```

返回示例：
```json
{
  "id": "abc123...",
  "title": "测试",
  "mode": "find_diff",
  "result_meta": {"match": 1, "diff_a": 1, "diff_b": 1, "total": 3, "duration_ms": 0.02}
}
```

### 🧠 对比算法

3 种模式 + 标准化函数：

```python
def diff(text_a, text_b, mode, options):
    list_a = parse(text_a)                              # 按行拆分
    list_b = parse(text_b)
    norm_a = [normalize(v, options) for v in list_a]    # trim/lowercase/skip_empty
    norm_b = [normalize(v, options) for v in list_b]
    # 根据 mode 输出 {rows, summary}
```

**模式差异**：
- **find_diff** · 列出所有差异行（A 有 B 没有 + B 有 A 没有）+ 共同行
- **vlookup** · 以 A 列为 key，查 B 列是否有匹配
- **intersect** · 只输出双侧都存在的值（去重后）

### ⚠️ 已知约束

- **数据规模** · 单列最多 1000 行、100,000 字符（服务端校验）
- **重复值语义** · 找差异按出现次数匹配；VLOOKUP 对 A 的每一行查询 B 的首个匹配；交集去重并按 A 首次出现顺序展示
- **历史保留期** · 90 天自动过期；启动时清理，过期任务不可访问、分享或导出
- **分享权限** · 分享链接是无登录的只读能力链接；持有者可在有效期内读取完整任务数据
- **管理员权限** · 不设置 `DIFF_LAB_ADMIN_TOKEN` 时保持本地开发兼容；公网环境应始终设置
- **SQLite 并发** · WAL 改善读写共存，但仍适合单实例、低到中等写入量，不适合高并发写入

### 📝 License

MIT — 详见 [LICENSE](LICENSE)

---

## English

### ✨ Features

- **3 compare modes** · Find Diff / VLOOKUP / Intersect
- **Side-by-side highlighting** · Diff rows colored + status badges
- **3 match options** · Ignore case / Trim whitespace / Skip empty
- **Bilingual UI** · Auto-detect browser language, one-click switch (top-right), localStorage persistence
- **History** · Auto-saved, 90-day retention
- **Share links** · Generate high-entropy tokens, no login required (7 days by default, capped by the task's 90-day retention, and revocable)
- **Safe export** · Streaming CSV with UTF-8 BOM and spreadsheet-formula injection protection
- **Access control** · Browser-scoped anonymous ownership, global admin management, and read-only sharing
- **Reliable SQLite** · WAL, foreign keys, busy timeout, expiry cleanup, and health checks
- **Schema migrations** · Alembic automatically upgrades the database schema at startup
- **Tested** · Automated coverage for API, migrations, security boundaries, and diff behavior

### 🚀 Quick Start

**Option 1 · Docker (recommended)**

```bash
export DIFF_LAB_ADMIN_TOKEN="$(openssl rand -hex 32)"
docker-compose up -d --build
```

Open http://localhost:8001

Data persisted in Docker volume `diff-lab-data` (SQLite file).

Regular users do not enter a token. The browser creates an anonymous identity and only receives its own task history. Enter the server token through **Configure admin token** to view and manage all tasks. See [docs/DEPLOY.md](docs/DEPLOY.md) for production guidance.

**Option 2 · Local development**

Backend:
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Frontend (new terminal):
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Run backend tests:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### 🌍 i18n

| Language | Code | File |
|---|---|---|
| 简体中文 | `zh-CN` | `frontend/src/i18n/locales/zh-CN.json` |
| English | `en-US` | `frontend/src/i18n/locales/en-US.json` |

**Detection order**: localStorage preference → `navigator.language` → default `zh-CN`.

**Add a new language**: copy `en-US.json` → translate → add to `SUPPORTED_LOCALES` in `src/i18n/index.js` → register in `messages`.

### 🏗️ Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Vue 3 + Vite 5 + vue-router 4 + axios + **vue-i18n 10** |
| Backend | Python 3.11 + FastAPI + SQLAlchemy + Alembic |
| Database | SQLite (single file, zero ops) |
| Deploy | Docker multi-stage build (static frontend embedded in Python image) |

### 🔌 API

| Method | Path | Purpose | Access |
|---|---|---|---|
| `POST` | `/api/tasks` | Create compare task | Anonymous identity |
| `GET` | `/api/tasks` | List own history; admins list all | Owner or admin |
| `GET` | `/api/tasks/{id}` | Get task detail | Owner or admin |
| `DELETE` | `/api/tasks/{id}` | Delete task | Admin |
| `GET` | `/api/tasks/{id}/export` | Export CSV | Owner or admin |
| `GET/POST/DELETE` | `/api/tasks/{id}/share` | Manage share link | Admin |
| `GET` | `/api/share/{token}` | Read-only access via share token | Share token |
| `POST` | `/api/preview` | Live preview (no DB write) | Public |

Full OpenAPI docs: visit `/docs` after launch.

Anonymous identity uses a 64-character hex `X-User-Token`; the web UI creates it automatically. Admin requests use either `Authorization: Bearer <token>` or `X-Admin-Token: <token>`.

### 🔐 Security & Operations

- **Anonymous identity** · The raw user token stays in browser `localStorage`; only its SHA-256 digest is stored in the database. Clearing browser data or changing devices loses access to that history.
- **Admin token** · Set `DIFF_LAB_ADMIN_TOKEN` on every public deployment. Admin endpoints return 503 when it is absent, and the UI validates the token before enabling admin mode.
- **Legacy tasks** · Tasks created before ownership was introduced remain admin-only.
- **Share links** · Valid for seven days by default; configurable from 1 to 90 days, capped by the parent task's 90-day retention, and revocable by an admin.
- **Input & export** · Each column is capped at 1,000 rows and 100,000 characters. Formula-prefixed CSV cells are escaped before export.
- **Traceability** · API responses include `X-Request-ID`, error bodies include the same request ID, and `/health` verifies database connectivity.
- **Database** · Startup runs Alembic migrations and removes expired records. SQLite uses WAL, foreign keys, and a busy timeout.

### ⚠️ Constraints

- **Data scale** · Each column is limited to 1,000 rows and 100,000 characters (server-enforced)
- **Duplicate policy** · Find Diff matches occurrences; VLOOKUP queries the first B match for each A row; Intersect is deduplicated in A's first-seen order
- **History retention** · 90 days; expired tasks are cleaned at startup and cannot be accessed, shared, or exported
- **Share access** · A share link is an unauthenticated read-only capability; anyone with it can read the full task during its validity period
- **Admin access** · Without `DIFF_LAB_ADMIN_TOKEN`, regular owner workflows still work but admin operations are disabled
- **SQLite concurrency** · WAL improves read/write coexistence, but this remains a single-instance, low-to-moderate write workload design

### 📝 License

MIT — see [LICENSE](LICENSE)
