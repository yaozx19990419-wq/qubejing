FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -yq --no-install-recommends -o Acquire::Retries=3 \
    build-essential gcc g++ make curl ca-certificates \
    libffi-dev libssl-dev \
    libjpeg-dev zlib1g-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 && \
    rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py .
COPY index.html .
COPY script.js .
COPY style.css .
COPY tailwind.config.js .
COPY about.html .
COPY privacy.html .
COPY robots.txt .
COPY sitemap.xml .
COPY img/ img/

# 在构建期预下载 rembg 模型到镜像内，避免运行时再下载（注意：会增大镜像体积）
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /home/app/.u2net \
    && curl -L -o /home/app/.u2net/u2net.onnx "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx" \
    && chown -R app:app /home/app /app

# 切换到非root用户
USER app

# 暴露端口
EXPOSE 8000

# Railway 会自动设置 PORT 环境变量
# 启动应用 - 使用环境变量中的端口，如果没有则使用8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
