# Diff.lab · 两列数据差异对比工具

> 像 VLOOKUP 一样好用，但更快、更直观、支持团队分享。
> Vue 3 + FastAPI + SQLite · 1000 行数据毫秒级对比 · 单镜像 Docker 部署 · 中英双语

![status](https://img.shields.io/badge/status-ready-success)
![license](https://img.shields.io/badge/license-MIT-blue)
![i18n](https://img.shields.io/badge/i18n-zh--CN%20%7C%20en--US-blue)
![docker](https://img.shields.io/badge/docker-ready-blue)

[English](#english) · [简体中文](#简体中文)

---

## 简体中文

### ✨ 功能

- **3 种对比模式** · 找差异 / VLOOKUP / 找交集
- **双列并排高亮** · 差异行染色 + 状态标签，视觉一眼可读
- **3 种匹配选项** · 忽略大小写 / 去空格 / 忽略空值
- **中英双语** · 自动检测浏览器语言，Hero 右上角一键切换，localStorage 持久化偏好
- **历史保存** · 自动持久化，90 天保留
- **分享链接** · 一键生成 8 位 token，无需登录
- **CSV 导出** · 流式下载，中文友好
- **单镜像部署** · Docker 多阶段构建，前端嵌入后端

### 🚀 快速启动

**方式 1 · Docker 单镜像（推荐）**

```bash
docker-compose up -d --build
```

打开 http://localhost:8001

数据持久化在 Docker volume `diff-lab-data`（SQLite 文件）。

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
| 后端 | Python 3.11 + FastAPI + SQLAlchemy |
| 数据库 | SQLite（单文件，零运维） |
| 部署 | Docker 多阶段构建（前端静态嵌入 Python 镜像） |

### 📁 项目结构

```
diff-lab/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 入口 + 静态前端挂载 + SPA 兜底
│   ├── db.py                   # SQLite 连接（支持 DIFF_LAB_DB 环境变量）
│   ├── models.py               # ORM 模型 + Pydantic Schema
│   ├── diff_engine.py          # 核心对比算法（3 模式 + 标准化）
│   ├── routers/
│   │   ├── tasks.py            # CRUD + 预览 + 分享 + 导出 CSV
│   │   └── share.py            # 通过 token 访问
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
│   │   │   ├── StepImport.vue        # 双列输入
│   │   │   ├── StepMode.vue          # 模式选择
│   │   │   └── StepResult.vue        # 结果表格
│   │   ├── i18n/
│   │   │   ├── index.js              # vue-i18n 配置 + 自动探测
│   │   │   └── locales/
│   │   │       ├── zh-CN.json        # 简体中文（76 keys）
│   │   │       └── en-US.json        # English（76 keys）
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

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/tasks` | 创建对比任务 |
| `GET` | `/api/tasks` | 列出所有任务 |
| `GET` | `/api/tasks/{id}` | 获取任务详情 |
| `DELETE` | `/api/tasks/{id}` | 删除任务 |
| `POST` | `/api/tasks/{id}/share` | 生成分享链接（8 位 token） |
| `GET` | `/api/share/{token}` | 通过分享链接访问（只读） |
| `GET` | `/api/tasks/{id}/export` | 导出 CSV |
| `POST` | `/api/preview` | 实时预览（不存 DB） |

完整 OpenAPI 文档：启动后访问 `/docs`

### 🧪 快速测试

```bash
curl -X POST http://localhost:8001/api/tasks \
  -H "Content-Type: application/json" \
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

- **数据规模** · 单次对比 ≤ 1000 行（性能兜底）
- **历史保留期** · 90 天自动过期（`expires_at` 字段）
- **分享权限** · 无鉴权，拿到链接即可访问（内部工具设计）
- **SQLite 并发** · 不支持高并发写入（单进程内部工具够用）

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
- **Share links** · Generate 8-char tokens, no login required
- **CSV export** · Streaming download, UTF-8 friendly
- **Single-image deploy** · Docker multi-stage build

### 🚀 Quick Start

**Option 1 · Docker (recommended)**

```bash
docker-compose up -d --build
```

Open http://localhost:8001

Data persisted in Docker volume `diff-lab-data` (SQLite file).

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
| Backend | Python 3.11 + FastAPI + SQLAlchemy |
| Database | SQLite (single file, zero ops) |
| Deploy | Docker multi-stage build (static frontend embedded in Python image) |

### 🔌 API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/tasks` | Create compare task |
| `GET` | `/api/tasks` | List all tasks |
| `GET` | `/api/tasks/{id}` | Get task detail |
| `DELETE` | `/api/tasks/{id}` | Delete task |
| `POST` | `/api/tasks/{id}/share` | Generate share link (8-char token) |
| `GET` | `/api/share/{token}` | Access via share token (read-only) |
| `GET` | `/api/tasks/{id}/export` | Export CSV |
| `POST` | `/api/preview` | Live preview (no DB write) |

Full OpenAPI docs: visit `/docs` after launch.

### ⚠️ Constraints

- **Data scale** · ≤ 1000 rows per compare (performance cap)
- **History retention** · 90 days auto-expire
- **Share auth** · No auth required (internal-tool design)
- **SQLite concurrency** · Single-process, not for high-write workloads

### 📝 License

MIT — see [LICENSE](LICENSE)