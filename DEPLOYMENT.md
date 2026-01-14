# ClearBG AI 部署指南

## 项目概述

ClearBG AI 是一个基于 FastAPI 和 rembg 的 AI 图像背景移除服务，支持单张和批量处理。

## 快速开始

### 使用 Docker 部署（推荐）

1. **克隆项目**

   ```bash
   git clone <your-repo-url>
   cd ai去背景
   ```

2. **构建和运行**

   ```bash
   # 生产环境
   ./deploy.sh production

   # 或手动构建
   docker-compose up --build -d
   ```

3. **验证部署**
   ```bash
   curl http://localhost:8000/docs
   ```

## 部署选项

### 1. Docker 容器部署

#### 本地开发

```bash
docker-compose up --build
```

#### 生产环境

```bash
# 使用部署脚本
./deploy.sh production

# 或手动部署
docker build -t clearbg-ai .
docker run -d --name clearbg-ai -p 8000:8000 --restart unless-stopped clearbg-ai
```

### 2. 服务器直接部署

#### 环境准备

```bash
# 安装 Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 使用 systemd 服务

```bash
# 复制服务文件
sudo cp clearbg.service /etc/systemd/system/
sudo systemctl daemon-reload

# 修改工作目录和用户
sudo nano /etc/systemd/system/clearbg.service

# 启动服务
sudo systemctl start clearbg
sudo systemctl enable clearbg
```

#### 使用 Nginx 反向代理

```bash
# 安装 Nginx
sudo apt install nginx

# 复制配置文件
sudo cp nginx.conf /etc/nginx/sites-available/clearbg
sudo ln -s /etc/nginx/sites-available/clearbg /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 云平台部署

#### Vercel (推荐前端)

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署静态文件
vercel --prod
```

#### Railway

1. 连接 GitHub 仓库
2. Railway 会自动检测 Python 项目
3. 设置环境变量
4. 部署完成

#### Render

1. 创建新 Web Service
2. 连接 GitHub 仓库
3. 设置构建命令: `pip install -r requirements.txt`
4. 设置启动命令: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Heroku

```bash
# 创建 Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 部署
git push heroku main
```

## 环境变量配置

创建 `.env` 文件：

```bash
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["https://clearbg.tech", "https://www.clearbg.tech"]
MAX_FILE_SIZE_MB=10
MAX_BATCH_SIZE=10
WORKERS=2
```

## 性能优化

### 服务器配置

- **CPU**: 至少 2 核心
- **内存**: 至少 2GB RAM
- **存储**: 至少 10GB SSD

### 扩展选项

- 使用 Gunicorn 替代 Uvicorn
- 配置 Nginx 负载均衡
- 添加 Redis 缓存
- 使用 CDN 分发静态文件

## 监控和维护

### 健康检查

```bash
# 检查服务状态
curl http://clearbg.tech/health

# 检查 API 文档
curl http://clearbg.tech/docs
```

### 日志查看

```bash
# Docker 日志
docker logs clearbg-ai

# Systemd 日志
sudo journalctl -u clearbg -f
```

### 备份策略

- 定期备份配置文件
- 监控磁盘使用情况
- 设置自动重启策略

## 安全考虑

1. **HTTPS**: 使用 SSL 证书
2. **防火墙**: 配置 UFW 或 iptables
3. **更新**: 定期更新系统和依赖
4. **监控**: 设置日志监控和告警

## 故障排除

### 常见问题

1. **端口占用**

   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **内存不足**

   ```bash
   free -h
   # 增加 swap 或升级服务器
   ```

3. **依赖问题**
   ```bash
   pip check
   pip install --force-reinstall -r requirements.txt
   ```

## 成本估算

### 免费选项（不推荐用于 AI 服务）

- **Railway**: 每月 512MB 免费额度（内存不足）
- **Render**: 每月 750 小时免费（按需付费更贵）
- **Vercel**: 前端免费，后端不适合 AI 处理

### 最经济选项

- **Railway Hobby**: $5/月 (512MB → 8GB 内存)
- **DigitalOcean Droplet**: $6/月 (1GB 内存共享 CPU)
- **Linode VPS**: $5/月 (1GB 内存)
- **AWS Lightsail**: $10/月 (1GB 内存)

### 推荐方案

1. **Railway Hobby** ($5/月) - 最简单，自动扩展
2. **DigitalOcean Droplet** ($6/月) - 最灵活，性价比最高

## 支持

如果遇到部署问题，请检查：

1. 系统要求（Python 3.11+）
2. 端口可用性
3. 防火墙设置
4. 环境变量配置
