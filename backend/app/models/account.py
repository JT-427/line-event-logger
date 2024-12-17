from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
import uuid
import enum

class AccountType(str, enum.Enum):
    INTERNAL = "internal"  # 內部人員
    EXTERNAL = "external"  # 外部人員
    UNKNOWN = "unknown"    # 未分類

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_user_id = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String)
    picture_url = Column(String)
    status_message = Column(String)
    account_type = Column(Enum(AccountType), default=AccountType.UNKNOWN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 