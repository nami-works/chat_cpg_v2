from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.auth.security import get_current_user
from app.models.user import User
from app.models.brand import Brand
from app.services.brand_service import BrandService


# MVP: Simplified brand models - only for reading
class BrandResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    website_url: Optional[str]
    blog_url: Optional[str]
    brand_description: Optional[str]
    style_guide: Optional[str]
    products_info: Optional[str]
    format_recommendations: Optional[str]
    knowledge_base: Optional[str]
    benchmarks: Optional[List[str]]
    is_active: bool

    class Config:
        from_attributes = True


# MVP: Comment out CRUD models for now
# class BrandCreate(BaseModel):
#     name: str
#     slug: str
#     website_url: Optional[str] = None
#     blog_url: Optional[str] = None
#     brand_description: Optional[str] = None
#     style_guide: Optional[str] = None
#     products_info: Optional[str] = None
#     format_recommendations: Optional[str] = None
#     knowledge_base: Optional[str] = None
#     benchmarks: Optional[List[str]] = None
#
#
# class BrandUpdate(BaseModel):
#     name: Optional[str] = None
#     website_url: Optional[str] = None
#     blog_url: Optional[str] = None
#     brand_description: Optional[str] = None
#     style_guide: Optional[str] = None
#     products_info: Optional[str] = None
#     format_recommendations: Optional[str] = None
#     knowledge_base: Optional[str] = None
#     benchmarks: Optional[List[str]] = None


router = APIRouter(prefix="/brands", tags=["brands"])


# MVP: Comment out brand creation for now
# @router.post("/", response_model=BrandResponse)
# async def create_brand(
#     brand_data: BrandCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Create a new brand"""
#     brand_service = BrandService(db)
#     
#     # Check if brand slug already exists
#     existing_brand = brand_service.get_brand_by_slug(brand_data.slug)
#     if existing_brand:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Brand with this slug already exists"
#         )
#     
#     brand = brand_service.create_brand(**brand_data.dict())
#     return brand


@router.get("/", response_model=List[BrandResponse])
async def get_brands(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all brands"""
    brand_service = BrandService(db)
    brands = brand_service.get_brands(skip=skip, limit=limit)
    return brands


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific brand"""
    brand_service = BrandService(db)
    brand = brand_service.get_brand_by_id(brand_id)
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    return brand


@router.get("/slug/{slug}", response_model=BrandResponse)
async def get_brand_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a brand by slug"""
    brand_service = BrandService(db)
    brand = brand_service.get_brand_by_slug(slug)
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    return brand


# MVP: Comment out brand modification endpoints for now
# @router.put("/{brand_id}", response_model=BrandResponse)
# async def update_brand(
#     brand_id: UUID,
#     brand_data: BrandUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Update a brand"""
#     brand_service = BrandService(db)
#     
#     # Only update fields that are provided
#     update_data = {k: v for k, v in brand_data.dict().items() if v is not None}
#     
#     brand = brand_service.update_brand(brand_id, **update_data)
#     
#     if not brand:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Brand not found"
#         )
#     
#     return brand
#
#
# @router.delete("/{brand_id}")
# async def delete_brand(
#     brand_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Delete a brand"""
#     brand_service = BrandService(db)
#     
#     success = brand_service.delete_brand(brand_id)
#     
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Brand not found"
#         )
#     
#     return {"message": "Brand deleted successfully"} 