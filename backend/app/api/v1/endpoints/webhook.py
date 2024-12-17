from fastapi import APIRouter, Header, Request, HTTPException
import hmac
import hashlib
import base64
from datetime import datetime
from app.core.config import settings
from app.models.message import LineEvent, Message, MessageType
from app.core.storage import StorageManager
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

def verify_signature(body: bytes, signature: str) -> bool:
    """驗證 LINE Webhook 簽章"""
    hash = hmac.new(
        settings.LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    calculated_signature = base64.b64encode(hash).decode('utf-8')
    return hmac.compare_digest(calculated_signature, signature)

async def handle_file_message(message_data: dict, storage_manager: StorageManager):
    """處理檔案類型的訊息（圖片、影片、音檔、一般檔案）"""
    message_type = message_data["type"]
    message_id = message_data["id"]
    
    # 根據訊息類型設定檔案副檔名和 content type
    file_extension = {
        "image": ".jpg",
        "video": ".mp4",
        "audio": ".m4a",
        "file": ""  # 一般檔案使用原始副檔名
    }.get(message_type, ".bin")
    
    content_type = {
        "image": "image/jpeg",
        "video": "video/mp4",
        "audio": "audio/m4a",
        "file": message_data.get("contentType", "application/octet-stream")
    }.get(message_type, "application/octet-stream")
    
    # 取得檔案名稱
    if message_type == "file":
        file_name = message_data.get("fileName", f"{message_id}.bin")
    else:
        file_name = f"{message_id}{file_extension}"
    
    file_content = await storage_manager.download_from_line(
        message_id=message_id,
        message_type=message_type
    )
    
    # 上傳至指定的雲端儲存空間
    file_info = await storage_manager.upload_file(
        file_content=file_content,
        file_name=file_name,
        content_type=content_type
    )
    
    return file_info

@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    """處理 LINE Webhook 事件"""
    logger.info("Received LINE webhook request")
    body = await request.body()
    
    if not verify_signature(body, x_line_signature):
        logger.error("Invalid signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    event_data = await request.json()
    logger.info(f"Received event data: {event_data}")
    storage_manager = StorageManager()
    
    for event in event_data.get("events", []):
        # 儲存原始事件
        line_event = LineEvent(
            webhook_event_id=event.get("webhookEventId"),
            destination=event_data.get("destination"),
            event_type=event.get("type"),
            timestamp=datetime.fromtimestamp(event.get("timestamp") / 1000),
            source=event.get("source", {}),
            message=event.get("message", {}),
            raw_data=event
        )
        line_event.save()
        
        # 如果是訊息事件，進行訊息處理
        if event.get("type") == "message":
            message_data = event["message"]
            message_type = message_data["type"]
            
            message = Message(
                message_id=message_data["id"],
                chat_type=event["source"]["type"],
                chat_id=event["source"].get("groupId") or event["source"].get("userId"),
                message_type=message_type,
                sender_id=event["source"].get("userId"),
                timestamp=datetime.fromtimestamp(event["timestamp"] / 1000),
                raw_data=message_data
            )
            
            # 根據訊息類型處理
            if message_type == MessageType.TEXT:
                message.text = message_data["text"]
                
            elif message_type == MessageType.STICKER:
                message.sticker_package_id = message_data["packageId"]
                message.sticker_id = message_data["stickerId"]
                
            elif message_type in [MessageType.IMAGE, MessageType.VIDEO, 
                                MessageType.AUDIO, MessageType.FILE]:
                file_info = await handle_file_message(message_data, storage_manager)
                message.file_id = file_info["id"]
                message.file_url = file_info["url"]
                message.original_file_name = file_info["original_name"]
                message.storage_file_name = file_info["name"]
                message.file_size = message_data.get("fileSize")
                message.file_content_type = file_info.get("contentType")
                
                if message_type in [MessageType.VIDEO, MessageType.AUDIO]:
                    message.duration = message_data.get("duration")
                if message_type == MessageType.VIDEO:
                    message.preview_url = file_info.get("preview_url")
                    
            elif message_type == MessageType.LOCATION:
                message.location_title = message_data["title"]
                message.location_address = message_data["address"]
                message.location_latitude = message_data["latitude"]
                message.location_longitude = message_data["longitude"]
            
            message.save()
    
    return {"message": "OK"} 