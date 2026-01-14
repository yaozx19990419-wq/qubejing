#!/bin/bash

# ClearBG AI 部署脚本
# 使用方法: ./deploy.sh [environment]
# 环境参数: development, staging, production (默认为 production)

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="clearbg-ai"
DOCKER_IMAGE="${PROJECT_NAME}:${ENVIRONMENT}"

echo "🚀 开始部署 ClearBG AI (${ENVIRONMENT} 环境)"

# 构建Docker镜像
echo "📦 构建Docker镜像..."
docker build -t $DOCKER_IMAGE .

# 停止现有容器
echo "🛑 停止现有容器..."
docker stop $PROJECT_NAME 2>/dev/null || true
docker rm $PROJECT_NAME 2>/dev/null || true

# 启动新容器
echo "▶️ 启动新容器..."
if [ "$ENVIRONMENT" = "production" ]; then
    # 生产环境配置
    docker run -d \
        --name $PROJECT_NAME \
        --restart unless-stopped \
        -p 8000:8000 \
        -e ENVIRONMENT=production \
        -e HOST=0.0.0.0 \
        -e PORT=8000 \
        $DOCKER_IMAGE
elif [ "$ENVIRONMENT" = "staging" ]; then
    # 预发布环境配置
    docker run -d \
        --name $PROJECT_NAME \
        --restart unless-stopped \
        -p 8001:8000 \
        -e ENVIRONMENT=staging \
        $DOCKER_IMAGE
else
    # 开发环境配置
    docker run -d \
        --name $PROJECT_NAME \
        -p 8000:8000 \
        -e ENVIRONMENT=development \
        $DOCKER_IMAGE
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 执行健康检查..."
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 部署成功! 服务运行在 http://localhost:8000"
else
    echo "❌ 部署失败，服务未能正常启动"
    docker logs $PROJECT_NAME
    exit 1
fi

echo "🎉 部署完成!"
