from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# 静态文件挂载与显式路由，确保部署环境（如 Railway）能返回顶级静态资源
# 挂载图片目录
app.mount("/img", StaticFiles(directory="img"), name="img")

# 显式返回顶级静态文件（与 index.html 同目录）
@app.get("/style.css")
async def style_css():
    return FileResponse("style.css")

@app.get("/script.js")
async def script_js():
    return FileResponse("script.js")

@app.get("/tailwind.config.js")
async def tailwind_config():
    return FileResponse("tailwind.config.js")

@app.get("/robots.txt")
async def robots_txt():
    return FileResponse("robots.txt")

@app.get("/sitemap.xml")
async def sitemap_xml():
    return FileResponse("sitemap.xml")

@app.get("/privacy.html")
async def privacy_html():
    return FileResponse("privacy.html")

@app.get("/about.html")
async def about_html():
    return FileResponse("about.html")

# 懒加载 rembg.remove（避免在模块导入时加载大模型，导致启动阻塞）
_rembg_remove = None

def ensure_rembg_loaded():
    global _rembg_remove
    if _rembg_remove is None:
        try:
            logger.info("Loading rembg model...")
            # 在函数体内导入，首次调用时会加载模型
            from rembg import remove as _remove_fn
            _rembg_remove = _remove_fn
            logger.info("rembg model loaded")
        except Exception:
            logger.exception("Failed to load rembg model")
            # keep _rembg_remove as None so callers know loading failed
            _rembg_remove = None

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
    try:
        logger.info(f"Received single file: {file.filename}")
        image_data = await file.read()

        # 尝试确保 rembg 可用
        ensure_rembg_loaded()

        if _rembg_remove is None:
            logger.warning("rembg not available, returning original file as fallback")
            # 返回原始文件字节作为回退（保留原 content_type）
            return Response(content=image_data, media_type=file.content_type or "application/octet-stream")

        try:
            output_data = _rembg_remove(image_data)
            return Response(content=output_data, media_type="image/png")
        except Exception:
            logger.exception("rembg processing failed for single file, returning original as fallback")
            return Response(content=image_data, media_type=file.content_type or "application/octet-stream")
    except Exception:
        logger.exception("remove-bg failed")
        return Response(content="Internal server error", status_code=500)

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
        logger.info(f"Received batch of {len(files)} files")
        ensure_rembg_loaded()
        for file in files:
            try:
                # 读取图片
                image_data = await file.read()

                # 如果 rembg 无法使用，直接把原始文件写入 ZIP 作为回退
                if _rembg_remove is None:
                    logger.warning("rembg not available, adding original file to zip as fallback")
                    original_name = os.path.splitext(file.filename)[0]
                    new_filename = f"{original_name}-Original{os.path.splitext(file.filename)[1] or '.png'}"
                    zip_file.writestr(new_filename, image_data)
                    continue

                # 尝试 AI 处理
                try:
                    output_data = _rembg_remove(image_data)
                    original_name = os.path.splitext(file.filename)[0]
                    new_filename = f"{original_name}-ClearBG.png"
                    zip_file.writestr(new_filename, output_data)
                except Exception:
                    logger.exception("rembg failed for one file in batch, adding original as fallback")
                    original_name = os.path.splitext(file.filename)[0]
                    new_filename = f"{original_name}-Original{os.path.splitext(file.filename)[1] or '.png'}"
                    zip_file.writestr(new_filename, image_data)
            except Exception:
                logger.exception("Failed to read/process one file in batch; skipping")

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