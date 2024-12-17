from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "LINE Message Logger"
    API_V1_STR: str = "/api/v1"
    
    # LINE Bot 設定
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str
    
    # PostgreSQL 設定
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # MongoDB 設定
    MONGODB_URL: str
    
    # 檔案儲存設定
    STORAGE_TYPE: str = "local"  # local, google_drive, sharepoint
    GOOGLE_DRIVE_CREDENTIALS: Optional[str] = None
    SHAREPOINT_CONFIG: Optional[dict] = None
    
    # SharePoint 設定
    SHAREPOINT_SITE_URL: Optional[str] = None
    SHAREPOINT_CLIENT_ID: Optional[str] = None
    SHAREPOINT_CLIENT_SECRET: Optional[str] = None
    SHAREPOINT_TENANT_ID: Optional[str] = None
    SHAREPOINT_DRIVE_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings() 