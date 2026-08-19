# 多阶段构建：Stage 1 构建前端，Stage 2 构建后端 + 嵌入前端静态文件
# 最终镜像：一个 Python 进程同时提供 API 和静态前端

# === Stage 1: 前端构建 ===
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# === Stage 2: 后端 + 嵌入前端 ===
FROM python:3.11-slim
WORKDIR /app

# 后端依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 复制前端构建产物到 FastAPI 静态目录
COPY --from=frontend-build /app/frontend/dist /app/static

# 数据目录（SQLite 文件 + 持久化）
RUN mkdir -p /app/data
ENV DIFF_LAB_DB=/app/data/diff_lab.db
ENV DIFF_LAB_PORT=8001

EXPOSE 8001

# 启动：uvicorn 挂载静态文件
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
