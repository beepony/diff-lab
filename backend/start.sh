#!/bin/bash
# 启动脚本（用 setsid 脱离当前 shell，避免被误判为 server）
cd /Users/bw/projects/diff-lab/backend
source venv/bin/activate
exec uvicorn main:app --host 127.0.0.1 --port 8001 --log-level info