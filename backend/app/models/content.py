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


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ContentProject(Base):
    __tablename__ = "content_projects"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    brand_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)  # Optional brand association
    
    # Project info
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=ProjectStatus.DRAFT.value)
    
    # Content themes and outputs
    themes = Column(JSON, default={})  # Dictionary of themes
    seo_themes = Column(JSON, default={})  # SEO-optimized themes
    macro_name = Column(String(200), nullable=True)  # Name for the theme set
    
    # Metadata
    meta = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    outputs = relationship("ContentOutput", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ContentProject(id={self.id}, name='{self.name}', status={self.status})>"


class OutputStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentOutput(Base):
    __tablename__ = "content_outputs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("content_projects.id"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Content data
    content = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    status = Column(String(50), default=OutputStatus.GENERATED.value)
    
    # Parsed content fields (extracted from AI output)
    themes = Column(JSON, default=[])  # List of content themes
    seo_themes = Column(JSON, default=[])  # List of SEO-focused themes
    macro_name = Column(String(200), nullable=True)  # Main content category/macro
    
    # AI generation metadata
    model_provider = Column(String(50), nullable=True)
    model_version = Column(String(100), nullable=True)
    prompt_used = Column(Text, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    
    # Metadata
    meta = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("ContentProject", back_populates="outputs")
    
    def __repr__(self):
        title_preview = self.title[:50] + "..." if self.title and len(self.title) > 50 else self.title
        return f"<ContentOutput(id={self.id}, title='{title_preview}', status={self.status})>" 