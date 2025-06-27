from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON

from ..db.database import Base


class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Basic brand information
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    website_url = Column(String(500), nullable=True)
    blog_url = Column(String(500), nullable=True)
    
    # Brand description and context
    brand_description = Column(Text, nullable=True)
    
    # Brand guidelines and materials
    style_guide = Column(Text, nullable=True)  # Brand writing style and voice guidelines
    products_info = Column(Text, nullable=True)  # Product information and descriptions
    format_recommendations = Column(Text, nullable=True)  # Content format guidelines
    
    # Reference brands for benchmarking
    benchmarks = Column(JSON, default=[])  # List of competitor/reference brands
    
    # Additional brand data
    meta = Column(JSON, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Brand(id={self.id}, name='{self.name}', slug='{self.slug}')>" 