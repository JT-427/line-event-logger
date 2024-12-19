from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, DictField, ListField, ReferenceField, IntField, FloatField

class MessageType(object):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    LOCATION = "location"
    STICKER = "sticker"
    TEMPLATE = "template"
    IMAGEMAP = "imagemap"
    FLEX = "flex"

class LineEvent(Document):
    """LINE Webhook 事件記錄"""
    meta = {
        'collection': 'line_events',
        'indexes': [
            'webhook_event_id',
            'timestamp',
            ('source.type', 'source.user_id', 'source.group_id'),
            'bot_id'
        ]
    }
    
    webhook_event_id = StringField(required=True, unique=True)
    destination = StringField(required=True)
    event_type = StringField(required=True)  # message, follow, unfollow 等
    timestamp = DateTimeField(required=True)
    source = DictField(required=True)  # 包含 type, user_id, group_id 等
    message = DictField()  # 如果是訊息事件，則包含訊息內容
    raw_data = DictField(required=True)  # 儲存完整的原始事件資料
    created_at = DateTimeField(default=datetime.utcnow)
    bot_id = StringField(required=True)  # LINE Bot 的 Channel ID

class Message(Document):
    """訊息記錄"""
    meta = {
        'collection': 'messages',
        'indexes': [
            'message_id',
            'timestamp',
            ('chat_type', 'chat_id'),
            'bot_id'
        ]
    }
    
    message_id = StringField(required=True, unique=True)
    chat_type = StringField(required=True)  # user, group
    chat_id = StringField(required=True)  # user_id 或 group_id
    message_type = StringField(required=True)  # 使用 MessageType 中定義的類型
    sender_id = StringField(required=True)
    timestamp = DateTimeField(required=True)
    
    # 文字訊息欄位
    text = StringField()
    
    # 貼圖訊息欄位
    sticker_package_id = StringField()
    sticker_id = StringField()
    
    # 圖片/影片/音檔/一般檔案共用欄位
    file_id = StringField()                 # 雲端儲存的檔案ID
    file_url = StringField()                # 雲端儲存的檔案URL
    original_file_name = StringField()      # 原始檔名
    storage_file_name = StringField()       # 儲存用的唯一檔名
    file_size = IntField()                  # 檔案大小
    file_content_type = StringField()       # 檔案類型
    
    # 影片/音檔專用欄位
    duration = IntField()                   # 播放長度(毫秒)
    preview_url = StringField()             # 預覽圖URL (影片用)
    
    # 位置訊息欄位
    location_title = StringField()
    location_address = StringField()
    location_latitude = FloatField()
    location_longitude = FloatField()
    
    # 原始資料
    raw_data = DictField(required=True)
    
    created_at = DateTimeField(default=datetime.utcnow)
    bot_id = StringField(required=True)  # LINE Bot 的 Channel ID