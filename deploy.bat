@echo off
REM ClearBG AI Windows 部署脚本
REM 使用方法: deploy.bat [environment]
REM 环境参数: development, staging, production (默认为 production)

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

set PROJECT_NAME=clearbg-ai
set DOCKER_IMAGE=%PROJECT_NAME%:%ENVIRONMENT%

echo 🚀 开始部署 ClearBG AI (%ENVIRONMENT% 环境)

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安装，请先安装 Docker
    exit /b 1
)

REM 构建Docker镜像
echo 📦 构建Docker镜像...
docker build -t %DOCKER_IMAGE% .

REM 停止现有容器
echo 🛑 停止现有容器...
docker stop %PROJECT_NAME% 2>nul
docker rm %PROJECT_NAME% 2>nul

REM 启动新容器
echo ▶️ 启动新容器...
if "%ENVIRONMENT%"=="production" (
    REM 生产环境配置
    docker run -d ^
        --name %PROJECT_NAME% ^
        --restart unless-stopped ^
        -p 8000:8000 ^
        -e ENVIRONMENT=production ^
        -e HOST=0.0.0.0 ^
        -e PORT=8000 ^
        %DOCKER_IMAGE%
) else if "%ENVIRONMENT%"=="staging" (
    REM 预发布环境配置
    docker run -d ^
        --name %PROJECT_NAME% ^
        --restart unless-stopped ^
        -p 8001:8000 ^
        -e ENVIRONMENT=staging ^
        %DOCKER_IMAGE%
) else (
    REM 开发环境配置
    docker run -d ^
        --name %PROJECT_NAME% ^
        -p 8000:8000 ^
        -e ENVIRONMENT=development ^
        %DOCKER_IMAGE%
)

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 健康检查
echo 🔍 执行健康检查...
curl -f http://localhost:8000/docs >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 部署成功! 服务运行在 http://localhost:8000
) else (
    echo ❌ 部署失败，服务未能正常启动
    docker logs %PROJECT_NAME%
    exit /b 1
)

echo 🎉 部署完成!
pause
