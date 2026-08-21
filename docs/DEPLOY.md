# 部署到 Azure Container Apps / 阿里云 / 任意 Docker 主机

## 1. 构建并推送镜像

```bash
# 登录容器 registry（以 Azure ACR 为例）
az acr login --name <your-acr-name>

# 给镜像打 tag
docker tag diff-lab <your-acr-name>.azurecr.io/diff-lab:v1.0
docker push <your-acr-name>.azurecr.io/diff-lab:v1.0
```

## 2. 部署到 Azure Container Apps

```bash
# 创建容器应用
az containerapp create \
  --name diff-lab \
  --resource-group <your-rg> \
  --environment <your-env> \
  --image <your-acr-name>.azurecr.io/diff-lab:v1.0 \
  --target-port 8001 \
  --ingress external \
  --registry-server <your-acr-name>.azurecr.io \
  --registry-username <username> \
  --registry-password <password>
```

## 3. 数据持久化

数据库默认写入容器内 `/app/data/diff_lab.db`，**重启会丢失**。
推荐挂载 Azure Files 或 host volume：

```bash
az containerapp update \
  --name diff-lab \
  --resource-group <your-rg> \
  --volume-name diff-lab-data \
  --volume-type AzureFile \
  --storage-account <your-storage> \
  --storage-account-key <your-key> \
  --storage-container diff-lab \
  --add-container-volume mount-path=/app/data
```

## 4. 自定义域名

在 Container Apps ingress 配置 `customDomain`：
```bash
az containerapp hostname add \
  --name diff-lab \
  --resource-group <your-rg> \
  --hostname diff.your-domain.com
```

## 5. 管理员令牌（公网部署必配）

设置一个足够长的随机值到 `DIFF_LAB_ADMIN_TOKEN`。公网部署必须配置：管理员使用它查看全部任务，并执行删除和分享管理；未配置时这些管理员接口会返回 503。

Docker Compose 示例：

```bash
export DIFF_LAB_ADMIN_TOKEN="$(openssl rand -hex 32)"
docker-compose up -d --build
```

管理员令牌仅在浏览器当前会话保存，并会在保存时向后端验证；通过页面右下角“配置管理员令牌”输入。不要将令牌提交到 Git 或写入前端构建变量。

普通用户无需手动配置。页面会自动生成匿名用户令牌并保存在当前浏览器的 `localStorage`；后端数据库只保存令牌摘要，并据此隔离历史、详情和导出。清除浏览器数据或换设备后，用户无法继续访问原身份的历史任务。升级前没有归属信息的旧任务仅管理员可见。

## 6. 备份

挂载的 SQLite 文件就是全部数据。定期下载即可：
```bash
az storage blob download \
  --account-name <your-storage> \
  --container-name diff-lab \
  --name diff_lab.db \
  --file backup-$(date +%Y%m%d).db
```
