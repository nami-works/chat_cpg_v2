import enum
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.database import Base


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentType(str, enum.Enum):
    """Document type classification."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    RTF = "rtf"
    ODT = "odt"
    OTHER = "other"


class KnowledgeBase(Base):
    """Knowledge base model."""
    __tablename__ = "knowledge_bases"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)  # List of tags
    
    # Configuration
    chunk_size = Column(Integer, default=1000)  # Characters per chunk
    chunk_overlap = Column(Integer, default=200)  # Overlap between chunks
    embedding_model = Column(String(100), default="text-embedding-ada-002")
    
    # Statistics (cached)
    total_documents = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    
    # Metadata
    meta = Column(JSON, default=dict)  # Additional settings and metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeBase(name='{self.name}', user_id='{self.user_id}')>"


class Document(Base):
    """Document model."""
    __tablename__ = "documents"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    knowledge_base_id = Column(PostgresUUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, etc.
    
    # Content information
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)  # Extracted text content
    content_length = Column(Integer, default=0)  # Character count
    
    # Processing status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    processing_error = Column(Text, nullable=True)
    
    # Vector search
    is_embedded = Column(Boolean, default=False)  # Whether chunks are in vector DB
    embedding_model = Column(String(100), nullable=True)
    
    # Metadata
    meta = Column(JSON, default=dict)  # File metadata, extraction info, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(filename='{self.filename}', status='{self.status}')>"


class DocumentChunk(Base):
    """Document chunk model for vector search."""
    __tablename__ = "document_chunks"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PostgresUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Chunk information
    chunk_index = Column(Integer, nullable=False)  # Order in document
    content = Column(Text, nullable=False)  # Chunk text content
    content_length = Column(Integer, nullable=False)  # Character count
    
    # Vector search
    vector_id = Column(String(255), nullable=True)  # ID in vector database
    embedding_model = Column(String(100), nullable=True)
    
    # Metadata
    meta = Column(JSON, default=dict)  # Chunk metadata, position info, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(index={self.chunk_index}, length={self.content_length})>"


class SearchQuery(Base):
    """Search query history for analytics."""
    __tablename__ = "search_queries"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    knowledge_base_id = Column(PostgresUUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=True)
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), default="semantic")  # semantic, keyword, hybrid
    
    # Results
    results_count = Column(Integer, default=0)
    top_score = Column(Float, nullable=True)
    avg_score = Column(Float, nullable=True)
    
    # Performance
    response_time_ms = Column(Integer, nullable=True)
    
    # Metadata
    meta = Column(JSON, default=dict)  # Search parameters, filters, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    knowledge_base = relationship("KnowledgeBase")

    def __repr__(self):
        return f"<SearchQuery(query='{self.query_text[:50]}...', results={self.results_count})>" 