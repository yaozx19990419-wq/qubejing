from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
import uvicorn
import io
import zipfile
import os
from typing import List # 引入 List 类型

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    uvicorn.run(app, host="0.0.0.0", port=8000)