from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mongoengine import connect
from app.core.config import settings
from app.api.v1.api import api_router
import time
from pymongo.errors import ConnectionFailure
from fastapi.staticfiles import StaticFiles
import os

def connect_to_mongodb(retries=5, delay=5):
    """嘗試連接到 MongoDB，如果失敗則重試"""
    for attempt in range(retries):
        try:
            connect(host=settings.MONGODB_URL)
            print("Successfully connected to MongoDB")
            return
        except ConnectionFailure as e:
            if attempt == retries - 1:  # 最後一次嘗試
                raise e
            print(f"Failed to connect to MongoDB. Retrying in {delay} seconds...")
            time.sleep(delay)

# 建立 FastAPI 應用程式
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設定靜態檔案服務
# 確保 storage 目錄存在
storage_dir = os.path.join(os.getcwd(), "storage")
if not os.path.exists(storage_dir):
    os.makedirs(storage_dir)

# 掛載 storage 目錄為靜態檔案服務
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")

# 連接 MongoDB（帶重試機制）
connect_to_mongodb()

# 註冊 API 路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "LINE Message Logger API",
        "version": "1.0.0",
        "docs_url": f"{settings.API_V1_STR}/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 