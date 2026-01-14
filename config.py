"""
生产环境配置文件
"""
import os
from typing import List

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 环境
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS配置
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", '["*"]')
CORS_ORIGINS: List[str] = eval(CORS_ORIGINS_STR)  # 在生产环境中应该更安全地解析

# 文件限制
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "10"))

# 性能配置
WORKERS = int(os.getenv("WORKERS", "1"))  # Gunicorn workers
