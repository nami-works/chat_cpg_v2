from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..auth.security import get_current_user
from ..db.database import get_db
from ..models.user import User
from ..services.knowledge_service import KnowledgeService
from ..services.file_service import FileService
from ..services.vector_service import VectorService

router = APIRouter()

# Initialize services
knowledge_service = KnowledgeService()
file_service = FileService()
vector_service = VectorService()


# Pydantic models
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    settings: Optional[dict] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    settings: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    knowledge_base_id: Optional[str] = None
    top_k: int = 10
    score_threshold: float = 0.7


# Knowledge Base Management Endpoints

@router.post("/knowledge-bases", response_model=dict)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new knowledge base."""
    try:
        kb = await knowledge_service.create_knowledge_base(
            name=kb_data.name,
            user_id=str(current_user.id),
            db=db,
            description=kb_data.description,
            tags=kb_data.tags,
            settings=kb_data.settings
        )
        
        return {
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "tags": kb.tags,
            "created_at": kb.created_at.isoformat(),
            "message": "Knowledge base created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create knowledge base: {str(e)}")


@router.get("/knowledge-bases", response_model=List[dict])
async def get_knowledge_bases(
    include_stats: bool = Query(True, description="Include real-time statistics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all knowledge bases for the current user."""
    try:
        return await knowledge_service.get_user_knowledge_bases(
            user_id=str(current_user.id),
            db=db,
            include_stats=include_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve knowledge bases: {str(e)}")


@router.get("/knowledge-bases/{kb_id}", response_model=dict)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific knowledge base."""
    try:
        kb = await knowledge_service.get_knowledge_base(kb_id, str(current_user.id), db)
        
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        return kb
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve knowledge base: {str(e)}")


@router.put("/knowledge-bases/{kb_id}", response_model=dict)
async def update_knowledge_base(
    kb_id: str,
    kb_data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a knowledge base."""
    try:
        success = await knowledge_service.update_knowledge_base(
            kb_id=kb_id,
            user_id=str(current_user.id),
            db=db,
            name=kb_data.name,
            description=kb_data.description,
            tags=kb_data.tags,
            settings=kb_data.settings
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        return {"message": "Knowledge base updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update knowledge base: {str(e)}")


@router.delete("/knowledge-bases/{kb_id}", response_model=dict)
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge base and all its content."""
    try:
        success = await knowledge_service.delete_knowledge_base(
            kb_id=kb_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        return {"message": "Knowledge base deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete knowledge base: {str(e)}")


# Document Management Endpoints

@router.get("/knowledge-bases/{kb_id}/documents", response_model=List[dict])
async def get_documents(
    kb_id: str,
    status: Optional[str] = Query(None, description="Filter by document status"),
    limit: int = Query(50, le=100, description="Maximum number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get documents in a knowledge base."""
    try:
        return await knowledge_service.get_documents(
            kb_id=kb_id,
            user_id=str(current_user.id),
            db=db,
            status=status,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.post("/knowledge-bases/{kb_id}/upload", response_model=dict)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None, description="Custom title for the document"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document to a knowledge base."""
    try:
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Upload file
        document = await file_service.upload_file(
            file=file,
            user_id=str(current_user.id),
            knowledge_base_id=kb_id,
            db=db,
            tags=tag_list,
            title=title
        )
        
        return {
            "id": str(document.id),
            "filename": document.original_filename,
            "title": document.title,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "status": document.status,
            "uploaded_at": document.uploaded_at.isoformat(),
            "message": "File uploaded successfully. Processing will begin shortly."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.get("/documents/{document_id}", response_model=dict)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a document."""
    try:
        document = await knowledge_service.get_document(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


@router.delete("/documents/{document_id}", response_model=dict)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document and all its associated data."""
    try:
        success = await knowledge_service.delete_document(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download the original document file."""
    try:
        # Get document info
        document = await knowledge_service.get_document(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file content
        file_content = await file_service.get_file_content(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not file_content:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Create streaming response
        def iter_file():
            yield file_content
        
        return StreamingResponse(
            iter_file(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={document['filename']}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")


# Search Endpoints

@router.post("/search", response_model=List[dict])
async def search_knowledge_base(
    search_data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search across knowledge base(s) using vector similarity."""
    try:
        results = await knowledge_service.search_knowledge_base(
            query=search_data.query,
            user_id=str(current_user.id),
            db=db,
            kb_id=search_data.knowledge_base_id,
            top_k=search_data.top_k,
            score_threshold=search_data.score_threshold
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/chunks/{chunk_id}", response_model=dict)
async def get_chunk_content(
    chunk_id: str,
    include_context: bool = Query(True, description="Include surrounding context"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get full content for a specific chunk."""
    try:
        chunk_content = await knowledge_service.get_chunk_content(
            chunk_id=chunk_id,
            user_id=str(current_user.id),
            db=db,
            include_context=include_context
        )
        
        if not chunk_content:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        return chunk_content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chunk content: {str(e)}")


# Analytics and Stats Endpoints

@router.get("/stats/vector", response_model=dict)
async def get_vector_stats(
    current_user: User = Depends(get_current_user)
):
    """Get vector database statistics for the user."""
    try:
        stats = await vector_service.get_vector_stats(str(current_user.id))
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve vector stats: {str(e)}")


# Utility Endpoints

@router.post("/documents/{document_id}/reprocess", response_model=dict)
async def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reprocess a document (re-extract content and create embeddings)."""
    try:
        # This would trigger document reprocessing
        # For now, return a message that it's not implemented
        raise HTTPException(
            status_code=501, 
            detail="Document reprocessing feature will be available in a future update"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reprocess document: {str(e)}")


@router.get("/supported-formats", response_model=dict)
async def get_supported_formats():
    """Get list of supported file formats and their limits."""
    from ..core.config import settings
    
    return {
        "supported_formats": settings.ALLOWED_FILE_TYPES,
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        "max_file_size_bytes": settings.MAX_FILE_SIZE,
        "embedding_model": "text-embedding-ada-002",
        "chunk_size": 1000,
        "chunk_overlap": 200
    } 