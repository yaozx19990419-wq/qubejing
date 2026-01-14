from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import io
import zipfile
import os
from typing import List  # 引入 List 类型
import logging
import os

# 配置类（简化，避免对 pydantic 版本的依赖）
class Settings:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.host = "0.0.0.0"
        self.port = int(os.getenv("PORT", "8000"))  # Railway 会设置 PORT
        cors = os.getenv("CORS_ORIGINS", "")
        # 如果需要多个 origin，用逗号分隔；默认允许所有
        self.cors_origins = cors.split(",") if cors else ["*"]
        self.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        self.max_batch_size = int(os.getenv("MAX_BATCH_SIZE", "10"))

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

# 懒加载 rembg.remove（避免在模块导入时加载大模型，导致启动阻塞）
_rembg_remove = None

def ensure_rembg_loaded():
    global _rembg_remove
    if _rembg_remove is None:
        # 在函数体内导入，首次调用时会加载模型
        from rembg import remove as _remove_fn
        _rembg_remove = _remove_fn

# 轻量健康检查接口，不触发 rembg 加载
@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

# 根路径返回 index.html（使自定义域访问根路径有内容）
@app.get("/")
async def root():
    return FileResponse("index.html")

# 1. 单张处理接口
@app.post("/api/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    image_data = await file.read()
    ensure_rembg_loaded()
    output_data = _rembg_remove(image_data)
    return Response(content=output_data, media_type="image/png")

# 2. 批量处理接口 (返回 ZIP)
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
        ensure_rembg_loaded()
        for file in files:
            # 读取图片
            image_data = await file.read()
            # AI 处理
            output_data = _rembg_remove(image_data)
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