from abc import ABC, abstractmethod
import aiohttp
from typing import Dict, Optional
import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from app.core.config import settings

class StorageFactory:
    """儲存服務工廠類"""
    
    @staticmethod
    def create_storage(storage_type: str = None) -> 'BaseStorage':
        """根據設定建立對應的儲存服務"""
        storage_type = storage_type or settings.STORAGE_TYPE.lower()
        
        if storage_type == "sharepoint":
            return SharePointStorage()
        elif storage_type == "google_drive":
            return GoogleDriveStorage()
        elif storage_type == "local":
            return LocalStorage()
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

class FileNameGenerator:
    """檔案名稱生成器"""
    
    @staticmethod
    def generate_unique_name(original_filename: str) -> str:
        """生成唯一的檔案名稱
        格式: {uuid}_{original_filename}
        """
        name, ext = os.path.splitext(original_filename)
        return f"{str(uuid.uuid4())}_{name}{ext}"

class BaseStorage(ABC):
    """儲存服務基礎類"""
    
    @abstractmethod
    async def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> dict:
        """上傳檔案到儲存空間"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """從儲存空間刪除檔案"""
        pass

class StorageResponse:
    """標準化的儲存服務回應"""
    def __init__(
        self,
        file_id: str,
        storage_file_name: str,
        original_file_name: str,
        file_url: str,
        content_type: str,
        size: int
    ):
        self.file_id = file_id
        self.storage_file_name = storage_file_name
        self.original_file_name = original_file_name
        self.file_url = file_url
        self.content_type = content_type
        self.size = size
    
    def to_dict(self) -> dict:
        return {
            "id": self.file_id,
            "name": self.storage_file_name,
            "original_name": self.original_file_name,
            "url": self.file_url,
            "contentType": self.content_type,
            "size": self.size
        }

class SharePointAuth:
    """SharePoint 認證管理器"""
    
    def __init__(self):
        self.tenant_id = settings.SHAREPOINT_TENANT_ID
        self.client_id = settings.SHAREPOINT_CLIENT_ID
        self.client_secret = settings.SHAREPOINT_CLIENT_SECRET
        self.token: Optional[Dict] = None
        self.token_expires: Optional[datetime] = None
    
    async def get_token(self) -> str:
        now = datetime.utcnow()
        if self.token and self.token_expires and self.token_expires > now:
            return self.token["access_token"]
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get SharePoint token: {error_text}")
                
                self.token = await response.json()
                self.token_expires = now + timedelta(seconds=int(self.token["expires_in"]) - 300)
                return self.token["access_token"]

class SharePointStorage(BaseStorage):
    """SharePoint 儲存服務"""
    
    def __init__(self):
        self.site_url = settings.SHAREPOINT_SITE_URL
        self.drive_id = settings.SHAREPOINT_DRIVE_ID
        self.folder_path = "LineRecorderData"  # 指定儲存資料夾
        self.auth = SharePointAuth()
    
    async def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> dict:
        try:
            access_token = await self.auth.get_token()
            storage_file_name = FileNameGenerator.generate_unique_name(file_name)
            
            # 確保有正確的 content type
            if not content_type:
                content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            
            # 確保資料夾存在
            await self._ensure_folder_exists()
            
            # 使用大檔案上傳 API
            upload_session_url = (
                f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}"
                f"/root:/{self.folder_path}/{storage_file_name}:/createUploadSession"
            )
            
            # 在建立上傳工作階段時加入檔案資訊
            session_body = {
                "@microsoft.graph.conflictBehavior": "rename",
                "fileSystemInfo": {"@odata.type": "microsoft.graph.fileSystemInfo"},
                "name": storage_file_name,
                "description": "",
                "file": {"@odata.type": "microsoft.graph.file"}
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # 建立上傳工作階段
                async with session.post(
                    upload_session_url, 
                    headers=headers,
                    json=session_body
                ) as response:
                    if response.status not in [200, 201]:
                        error_data = await response.text()
                        print(f"Failed to create upload session: {error_data}")
                        raise Exception("Failed to create upload session")
                    
                    session_data = await response.json()
                    upload_url = session_data["uploadUrl"]
                
                # 上傳檔案
                upload_headers = {
                    "Content-Length": str(len(file_content)),
                    "Content-Range": f"bytes 0-{len(file_content)-1}/{len(file_content)}",
                    "Content-Type": content_type  # 設定正確的 content type
                }
                
                async with session.put(upload_url, headers=upload_headers, data=file_content) as upload_response:
                    if upload_response.status not in [200, 201]:
                        error_data = await upload_response.text()
                        print(f"Failed to upload file: {error_data}")
                        raise Exception("Failed to upload file content")
                    
                    file_data = await upload_response.json()
                    
                    return StorageResponse(
                        file_id=file_data["id"],
                        storage_file_name=storage_file_name,
                        original_file_name=file_name,
                        file_url=file_data["webUrl"],
                        content_type=content_type,  # 使用我們確定的 content type
                        size=file_data.get("size", len(file_content))
                    ).to_dict()
        
        except Exception as e:
            print(f"SharePoint upload error: {str(e)}")
            raise Exception(f"Failed to upload file to SharePoint: {str(e)}") from e
    
    async def _ensure_folder_exists(self):
        """確保目標資料夾存在，如果不存在則建立"""
        try:
            access_token = await self.auth.get_token()
            
            # 檢查資料夾是否存在
            check_url = (
                f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}"
                f"/root:/{self.folder_path}"
            )
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(check_url, headers=headers) as response:
                    if response.status == 404:
                        # 資料夾不存在，建立它
                        create_url = (
                            f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root/children"
                        )
                        
                        folder_data = {
                            "name": self.folder_path,
                            "folder": {},
                            "@microsoft.graph.conflictBehavior": "replace"
                        }
                        
                        async with session.post(create_url, headers=headers, json=folder_data) as create_response:
                            if create_response.status not in [200, 201]:
                                error_data = await create_response.json()
                                raise Exception(f"Failed to create folder in SharePoint: {error_data}")
                    
                    elif response.status not in [200, 201]:
                        error_data = await response.json()
                        raise Exception(f"Failed to check folder in SharePoint: {error_data}")
        
        except Exception as e:
            print(f"SharePoint folder check/create error: {str(e)}")
            raise Exception("Failed to ensure folder exists in SharePoint") from e
    
    async def delete_file(self, file_id: str) -> bool:
        try:
            access_token = await self.auth.get_token()
            delete_url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/items/{file_id}"
            
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(delete_url, headers=headers) as response:
                    return response.status == 204
        except Exception as e:
            print(f"SharePoint delete error: {str(e)}")
            return False

class LocalStorage(BaseStorage):
    """本地檔案系統儲存服務"""
    
    def __init__(self):
        self.storage_dir = os.path.join(os.getcwd(), "storage")
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """確保儲存目錄存在"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    async def upload_file(self, file_content: bytes, file_name: str, content_type: str) -> dict:
        try:
            # 生成唯一的檔案名稱
            storage_file_name = FileNameGenerator.generate_unique_name(file_name)
            file_path = os.path.join(self.storage_dir, storage_file_name)
            
            # 確保有正確的 content type
            if not content_type:
                content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            
            # 寫入檔案
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 取得檔案大小
            file_size = os.path.getsize(file_path)
            
            # 生成檔案 URL（使用相對路徑）
            file_url = f"/storage/{storage_file_name}"
            
            return StorageResponse(
                file_id=storage_file_name,  # 使用檔案名稱作為 ID
                storage_file_name=storage_file_name,
                original_file_name=file_name,
                file_url=file_url,
                content_type=content_type,
                size=file_size
            ).to_dict()
        
        except Exception as e:
            print(f"Local storage upload error: {str(e)}")
            raise Exception(f"Failed to upload file to local storage: {str(e)}") from e
    
    async def delete_file(self, file_id: str) -> bool:
        try:
            file_path = os.path.join(self.storage_dir, file_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Local storage delete error: {str(e)}")
            return False

class StorageManager:
    """儲存管理器"""
    
    def __init__(self):
        self.storage = StorageFactory.create_storage()
    
    async def download_from_line(self, message_id: str, message_type: str) -> bytes:
        """從 LINE 平台下載檔案"""
        url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        headers = {
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                return await response.read()
    
    async def upload_file(self, file_content: bytes, file_name: str, content_type: str = None) -> dict:
        """上傳檔案到指定的儲存空間"""
        if not content_type:
            content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        return await self.storage.upload_file(file_content, file_name, content_type)
    
    async def delete_file(self, file_id: str) -> bool:
        """刪除檔案"""
        return await self.storage.delete_file(file_id)