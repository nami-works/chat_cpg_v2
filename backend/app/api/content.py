from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.auth.security import get_current_user
from app.models.user import User
from app.models.content import ContentProject, ContentOutput
from app.services.content_service import ContentService


class ContentProjectCreate(BaseModel):
    name: str
    project_type: str = "redacao"
    description: Optional[str] = None
    brand_id: Optional[UUID] = None


class ContentProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    themes: Optional[Dict[str, str]] = None
    seo_themes: Optional[Dict[str, str]] = None
    macro_name: Optional[str] = None
    status: Optional[str] = None


class ContentProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    project_type: str
    themes: Optional[Dict[str, str]]
    seo_themes: Optional[Dict[str, str]]
    macro_name: Optional[str]
    status: str
    brand_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentOutputResponse(BaseModel):
    id: UUID
    theme_key: str
    theme_title: str
    content_type: str
    title: Optional[str]
    content: Optional[str]
    seo_title: Optional[str]
    meta_description: Optional[str]
    h1_tag: Optional[str]
    h2_tags: Optional[List[str]]
    keywords: Optional[List[str]]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ParseOutputsRequest(BaseModel):
    response_text: str


class CreateOutputsRequest(BaseModel):
    project_id: UUID


router = APIRouter(prefix="/content", tags=["content"])


@router.post("/projects", response_model=ContentProjectResponse)
async def create_project(
    project_data: ContentProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new content project"""
    content_service = ContentService(db)
    
    project = content_service.create_project(
        user_id=current_user.id,
        **project_data.dict()
    )
    
    return project


@router.get("/projects", response_model=List[ContentProjectResponse])
async def get_user_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all projects for the current user"""
    content_service = ContentService(db)
    projects = content_service.get_user_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return projects


@router.get("/projects/{project_id}", response_model=ContentProjectResponse)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project"""
    content_service = ContentService(db)
    project = content_service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user owns the project
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    return project


@router.put("/projects/{project_id}", response_model=ContentProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ContentProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    content_service = ContentService(db)
    project = content_service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this project"
        )
    
    # Update project with provided data
    update_data = {k: v for k, v in project_data.dict().items() if v is not None}
    
    if update_data:
        for key, value in update_data.items():
            setattr(project, key, value)
        
        db.commit()
        db.refresh(project)
    
    return project


@router.post("/projects/{project_id}/parse-outputs")
async def parse_creative_outputs(
    project_id: UUID,
    request: ParseOutputsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Parse creative outputs from AI response"""
    content_service = ContentService(db)
    project = content_service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this project"
        )
    
    # Parse the response
    parsed_data = content_service.parse_creative_outputs(
        request.response_text,
        project_id
    )
    
    return {
        "success": True,
        "parsed_data": parsed_data,
        "message": "Creative outputs parsed successfully"
    }


@router.post("/projects/{project_id}/create-outputs", response_model=List[ContentOutputResponse])
async def create_content_outputs(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create content outputs for all themes in a project"""
    content_service = ContentService(db)
    project = content_service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this project"
        )
    
    if not project.themes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have themes before creating outputs"
        )
    
    outputs = content_service.create_content_outputs(project_id)
    
    return outputs


@router.get("/projects/{project_id}/outputs", response_model=List[ContentOutputResponse])
async def get_project_outputs(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all content outputs for a project"""
    content_service = ContentService(db)
    project = content_service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    outputs = content_service.get_project_outputs(project_id)
    
    return outputs


@router.get("/outputs/{output_id}", response_model=ContentOutputResponse)
async def get_content_output(
    output_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific content output"""
    output = db.query(ContentOutput).filter(ContentOutput.id == output_id).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content output not found"
        )
    
    # Check if user owns the project
    if output.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this content"
        )
    
    return output


@router.put("/outputs/{output_id}", response_model=ContentOutputResponse)
async def update_content_output(
    output_id: UUID,
    title: Optional[str] = None,
    content: Optional[str] = None,
    seo_title: Optional[str] = None,
    meta_description: Optional[str] = None,
    h1_tag: Optional[str] = None,
    h2_tags: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update content output"""
    content_service = ContentService(db)
    output = db.query(ContentOutput).filter(ContentOutput.id == output_id).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content output not found"
        )
    
    if output.project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this content"
        )
    
    updated_output = content_service.update_content_output(
        output_id=output_id,
        title=title,
        content=content,
        seo_title=seo_title,
        meta_description=meta_description,
        h1_tag=h1_tag,
        h2_tags=h2_tags,
        keywords=keywords,
        status=status
    )
    
    return updated_output 