from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
import uvicorn
import io
import zipfile
import os
from typing import List # 引入 List 类型
import logging
from pydantic import BaseSettings

# 配置类
class Settings(BaseSettings):
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8000"))  # Railway 会设置 PORT
    cors_origins: list = ["*"]
    max_file_size_mb: int = 10
    max_batch_size: int = 10

    class Config:
        env_file = ".env"

settings = Settings()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. 单张处理接口 (保持不变)
@app.post("/api/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    image_data = await file.read()
    output_data = remove(image_data)
    return Response(content=output_data, media_type="image/png")

# 2. [新增] 批量处理接口 (返回 ZIP)
@app.post("/api/remove-bg-batch")
async def remove_background_batch(files: List[UploadFile] = File(...)):
    # 验证文件数量
    if len(files) > settings.max_batch_size:
        return Response(
            content=f"Maximum {settings.max_batch_size} files allowed per batch",
            status_code=400,
            media_type="text/plain"
        )

    # 创建一个内存里的 ZIP 文件
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            # 读取图片
            image_data = await file.read()
            
            # AI 处理
            output_data = remove(image_data)
            
            # 生成新文件名 (原名.png)
            original_name = os.path.splitext(file.filename)[0]
            new_filename = f"{original_name}-ClearBG.png"
            
            # 写入 ZIP
            zip_file.writestr(new_filename, output_data)
    
    # 指针归零，准备发送
    zip_buffer.seek(0)
    
    # 返回 ZIP 文件流
    return Response(
        content=zip_buffer.getvalue(), 
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=images.zip"}
    )

if __name__ == "__main__":
    logger.info(f"Starting server in {settings.environment} mode")
    logger.info(f"Server will run on {settings.host}:{settings.port}")
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info" if settings.environment == "production" else "debug"
    )