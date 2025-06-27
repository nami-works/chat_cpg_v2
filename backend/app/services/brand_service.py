from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.brand import Brand


class BrandService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_brand(
        self, 
        name: str, 
        slug: str,
        website_url: Optional[str] = None,
        blog_url: Optional[str] = None,
        brand_description: Optional[str] = None,
        style_guide: Optional[str] = None,
        products_info: Optional[str] = None,
        format_recommendations: Optional[str] = None,
        knowledge_base: Optional[str] = None,
        benchmarks: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Brand:
        """Create a new brand"""
        db_brand = Brand(
            name=name,
            slug=slug,
            website_url=website_url,
            blog_url=blog_url,
            brand_description=brand_description,
            style_guide=style_guide,
            products_info=products_info,
            format_recommendations=format_recommendations,
            knowledge_base=knowledge_base,
            benchmarks=benchmarks or [],
            metadata=metadata or {}
        )
        
        self.db.add(db_brand)
        self.db.commit()
        self.db.refresh(db_brand)
        
        return db_brand
    
    def get_brand_by_id(self, brand_id: UUID) -> Optional[Brand]:
        """Get brand by ID"""
        return self.db.query(Brand).filter(Brand.id == brand_id).first()
    
    def get_brand_by_slug(self, slug: str) -> Optional[Brand]:
        """Get brand by slug"""
        return self.db.query(Brand).filter(Brand.slug == slug).first()
    
    def get_brands(self, skip: int = 0, limit: int = 100) -> List[Brand]:
        """Get all brands with pagination"""
        return self.db.query(Brand).filter(Brand.is_active == True).offset(skip).limit(limit).all()
    
    def update_brand(self, brand_id: UUID, **updates) -> Optional[Brand]:
        """Update brand information"""
        brand = self.get_brand_by_id(brand_id)
        if not brand:
            return None
        
        for key, value in updates.items():
            if hasattr(brand, key):
                setattr(brand, key, value)
        
        self.db.commit()
        self.db.refresh(brand)
        
        return brand
    
    def delete_brand(self, brand_id: UUID) -> bool:
        """Soft delete a brand"""
        brand = self.get_brand_by_id(brand_id)
        if not brand:
            return False
        
        brand.is_active = False
        self.db.commit()
        
        return True 