from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

Base = declarative_base()


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AIModel(str, Enum):
    # OpenAI Models
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    
    # Groq Models
    LLAMA_3_70B = "llama-3.1-70b-versatile"
    LLAMA_3_8B = "llama-3.1-8b-instant"
    MIXTRAL_8X7B = "mixtral-8x7b-32768"
    
    # Anthropic Models
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    brand_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    project_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    
    # Conversation info
    title = Column(String(500), nullable=False)
    function_type = Column(String(50), default="general")  # general, redacao, oraculo
    status = Column(String(50), default=ConversationStatus.ACTIVE.value)
    
    # AI configuration
    model_provider = Column(String(50), default="openai")
    model_name = Column(String(100), default="gpt-4o-mini")
    reference = Column(String(50), default="ryb")
    api_key = Column(String(500), nullable=True)  # Encrypted API key
    
    # Metadata
    meta = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', function_type={self.function_type})>"


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Message content
    content = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)  # True for user, False for AI
    
    # AI generation metadata
    model_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    
    # Message metadata
    meta_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, is_user={self.is_user}, content='{content_preview}')>" 