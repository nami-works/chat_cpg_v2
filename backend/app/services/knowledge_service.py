import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from fastapi import HTTPException

from ..models.knowledge import (
    KnowledgeBase, Document, DocumentChunk, DocumentStatus, SearchQuery
)
from ..models.user import User
from .file_service import FileService
from .vector_service import VectorService
from .usage_service import UsageService

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self):
        self.file_service = FileService()
        self.vector_service = VectorService()
        self.usage_service = UsageService()
    
    async def create_knowledge_base(
        self,
        name: str,
        user_id: str,
        db: AsyncSession,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBase:
        """
        Create a new knowledge base.
        """
        # Check if name already exists for user
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.user_id == uuid.UUID(user_id),
                KnowledgeBase.name == name
            )
        )
        
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Knowledge base with this name already exists"
            )
        
        # Create knowledge base
        kb = KnowledgeBase(
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            tags=tags or [],
            metadata=settings or {}
        )
        
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
        
        logger.info(f"Created knowledge base {kb.id} for user {user_id}")
        return kb
    
    async def get_user_knowledge_bases(
        self,
        user_id: str,
        db: AsyncSession,
        include_stats: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all knowledge bases for a user.
        """
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.user_id == uuid.UUID(user_id)
            ).order_by(KnowledgeBase.updated_at.desc())
        )
        
        knowledge_bases = result.scalars().all()
        kb_list = []
        
        for kb in knowledge_bases:
            kb_data = {
                "id": str(kb.id),
                "name": kb.name,
                "description": kb.description,
                "tags": kb.tags,
                "total_documents": kb.total_documents,
                "total_size_bytes": kb.total_size_bytes,
                "total_chunks": kb.total_chunks,
                "created_at": kb.created_at.isoformat(),
                "updated_at": kb.updated_at.isoformat(),
                "last_accessed": kb.last_accessed.isoformat() if kb.last_accessed else None
            }
            
            if include_stats:
                # Get real-time stats
                stats = await self._get_knowledge_base_stats(kb.id, db)
                kb_data.update(stats)
            
            kb_list.append(kb_data)
        
        return kb_list
    
    async def get_knowledge_base(
        self,
        kb_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific knowledge base with details.
        """
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == uuid.UUID(kb_id),
                KnowledgeBase.user_id == uuid.UUID(user_id)
            )
        )
        
        kb = result.scalar_one_or_none()
        if not kb:
            return None
        
        # Update last accessed
        await db.execute(
            update(KnowledgeBase)
            .where(KnowledgeBase.id == uuid.UUID(kb_id))
            .values(last_accessed=datetime.utcnow())
        )
        await db.commit()
        
        # Get detailed stats
        stats = await self._get_knowledge_base_stats(kb.id, db)
        recent_documents = await self._get_recent_documents(kb.id, user_id, db, limit=5)
        
        return {
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "tags": kb.tags,
            "metadata": kb.meta,
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
            "embedding_model": kb.embedding_model,
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "stats": stats,
            "recent_documents": recent_documents
        }
    
    async def update_knowledge_base(
        self,
        kb_id: str,
        user_id: str,
        db: AsyncSession,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update knowledge base information.
        """
        # Check if knowledge base exists
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == uuid.UUID(kb_id),
                KnowledgeBase.user_id == uuid.UUID(user_id)
            )
        )
        
        kb = result.scalar_one_or_none()
        if not kb:
            return False
        
        # Check name uniqueness if changing name
        if name and name != kb.name:
            name_check = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.user_id == uuid.UUID(user_id),
                    KnowledgeBase.name == name,
                    KnowledgeBase.id != uuid.UUID(kb_id)
                )
            )
            
            if name_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail="Knowledge base with this name already exists"
                )
        
        # Update fields
        update_data = {"updated_at": datetime.utcnow()}
        
        if name:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if tags is not None:
            update_data["tags"] = tags
        if settings:
            update_data["metadata"] = {**kb.meta, **settings}
        
        await db.execute(
            update(KnowledgeBase)
            .where(KnowledgeBase.id == uuid.UUID(kb_id))
            .values(**update_data)
        )
        
        await db.commit()
        return True
    
    async def delete_knowledge_base(
        self,
        kb_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Delete a knowledge base and all its content.
        """
        # Get all documents in the knowledge base
        result = await db.execute(
            select(Document).where(
                Document.knowledge_base_id == uuid.UUID(kb_id),
                Document.user_id == uuid.UUID(user_id)
            )
        )
        
        documents = result.scalars().all()
        
        # Delete each document (this will handle files and vectors)
        for doc in documents:
            await self.delete_document(str(doc.id), user_id, db)
        
        # Delete the knowledge base
        await db.execute(
            delete(KnowledgeBase).where(
                KnowledgeBase.id == uuid.UUID(kb_id),
                KnowledgeBase.user_id == uuid.UUID(user_id)
            )
        )
        
        await db.commit()
        logger.info(f"Deleted knowledge base {kb_id} and {len(documents)} documents")
        return True
    
    async def get_documents(
        self,
        kb_id: str,
        user_id: str,
        db: AsyncSession,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get documents in a knowledge base.
        """
        query = select(Document).where(
            Document.knowledge_base_id == uuid.UUID(kb_id),
            Document.user_id == uuid.UUID(user_id)
        )
        
        if status:
            query = query.where(Document.status == status)
        
        query = query.order_by(Document.uploaded_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        doc_list = []
        for doc in documents:
            doc_list.append({
                "id": str(doc.id),
                "filename": doc.original_filename,
                "title": doc.title,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "content_preview": doc.content_preview,
                "total_pages": doc.total_pages,
                "word_count": doc.word_count,
                "total_chunks": doc.total_chunks,
                "chunks_processed": doc.chunks_processed,
                "tags": doc.tags,
                "is_sensitive": doc.is_sensitive,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "processing_started_at": doc.processing_started_at.isoformat() if doc.processing_started_at else None,
                "processing_completed_at": doc.processing_completed_at.isoformat() if doc.processing_completed_at else None,
                "processing_error": doc.processing_error,
                "last_accessed": doc.last_accessed.isoformat() if doc.last_accessed else None
            })
        
        return doc_list
    
    async def get_document(
        self,
        document_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a document.
        """
        result = await db.execute(
            select(Document).where(
                Document.id == uuid.UUID(document_id),
                Document.user_id == uuid.UUID(user_id)
            )
        )
        
        doc = result.scalar_one_or_none()
        if not doc:
            return None
        
        # Update last accessed
        await db.execute(
            update(Document)
            .where(Document.id == uuid.UUID(document_id))
            .values(last_accessed=datetime.utcnow())
        )
        await db.commit()
        
        # Get chunks
        chunks_result = await db.execute(
            select(DocumentChunk).where(
                DocumentChunk.document_id == uuid.UUID(document_id)
            ).order_by(DocumentChunk.chunk_index).limit(10)  # First 10 chunks
        )
        chunks = chunks_result.scalars().all()
        
        return {
            "id": str(doc.id),
            "knowledge_base_id": str(doc.knowledge_base_id),
            "filename": doc.original_filename,
            "title": doc.title,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "content_preview": doc.content_preview,
            "total_pages": doc.total_pages,
            "word_count": doc.word_count,
            "total_chunks": doc.total_chunks,
            "chunks_processed": doc.chunks_processed,
            "metadata": doc.meta,
            "tags": doc.tags,
            "is_sensitive": doc.is_sensitive,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "processing_started_at": doc.processing_started_at.isoformat() if doc.processing_started_at else None,
            "processing_completed_at": doc.processing_completed_at.isoformat() if doc.processing_completed_at else None,
            "processing_error": doc.processing_error,
            "last_accessed": datetime.utcnow().isoformat(),
            "chunks": [
                {
                    "id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "content_preview": chunk.content[:200],
                    "content_length": chunk.content_length,
                    "page_number": chunk.page_number,
                    "has_embedding": chunk.vector_id is not None
                }
                for chunk in chunks
            ]
        }
    
    async def delete_document(
        self,
        document_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Delete a document and all its associated data.
        """
        # Delete vectors first
        await self.vector_service.delete_document_vectors(document_id, user_id, db)
        
        # Delete file from storage
        await self.file_service.delete_file(document_id, user_id, db)
        
        # Delete chunks
        await db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == uuid.UUID(document_id),
                DocumentChunk.user_id == uuid.UUID(user_id)
            )
        )
        
        # Delete document record
        await db.execute(
            delete(Document).where(
                Document.id == uuid.UUID(document_id),
                Document.user_id == uuid.UUID(user_id)
            )
        )
        
        await db.commit()
        logger.info(f"Deleted document {document_id}")
        return True
    
    async def search_knowledge_base(
        self,
        query: str,
        user_id: str,
        db: AsyncSession,
        kb_id: Optional[str] = None,
        top_k: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search across knowledge base(s) using vector similarity.
        """
        # Use vector service for similarity search
        vector_results = await self.vector_service.search_similar_content(
            query=query,
            user_id=user_id,
            knowledge_base_id=kb_id,
            top_k=top_k,
            score_threshold=score_threshold,
            db=db
        )
        
        # Enhance results with additional document information
        enhanced_results = []
        for result in vector_results:
            # Get document info
            doc_result = await db.execute(
                select(Document).where(
                    Document.id == uuid.UUID(result["document_id"])
                )
            )
            doc = doc_result.scalar_one_or_none()
            
            if doc:
                enhanced_result = {
                    **result,
                    "document_title": doc.title,
                    "document_filename": doc.original_filename,
                    "document_type": doc.file_type,
                    "document_tags": doc.tags,
                    "chunk_content": None  # Will be loaded on demand
                }
                enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    async def get_chunk_content(
        self,
        chunk_id: str,
        user_id: str,
        db: AsyncSession,
        include_context: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get full content for a specific chunk.
        """
        return await self.vector_service.get_chunk_content(
            chunk_id, user_id, db, include_context
        )
    
    async def _get_knowledge_base_stats(
        self,
        kb_id: uuid.UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get real-time statistics for a knowledge base.
        """
        # Count documents by status
        status_counts = await db.execute(
            select(
                Document.status,
                func.count(Document.id).label('count')
            ).where(
                Document.knowledge_base_id == kb_id
            ).group_by(Document.status)
        )
        
        status_stats = {row.status: row.count for row in status_counts}
        
        # Total size and chunks
        totals = await db.execute(
            select(
                func.sum(Document.file_size).label('total_size'),
                func.sum(Document.total_chunks).label('total_chunks'),
                func.count(Document.id).label('total_documents')
            ).where(
                Document.knowledge_base_id == kb_id,
                Document.status != DocumentStatus.DELETED.value
            )
        )
        
        totals_row = totals.first()
        
        return {
            "status_breakdown": status_stats,
            "total_documents": totals_row.total_documents or 0,
            "total_size_bytes": totals_row.total_size or 0,
            "total_chunks": totals_row.total_chunks or 0,
            "processing_documents": status_stats.get(DocumentStatus.PROCESSING.value, 0),
            "failed_documents": status_stats.get(DocumentStatus.FAILED.value, 0)
        }
    
    async def _get_recent_documents(
        self,
        kb_id: uuid.UUID,
        user_id: str,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent documents in a knowledge base.
        """
        result = await db.execute(
            select(Document).where(
                Document.knowledge_base_id == kb_id,
                Document.user_id == uuid.UUID(user_id),
                Document.status != DocumentStatus.DELETED.value
            ).order_by(Document.uploaded_at.desc()).limit(limit)
        )
        
        documents = result.scalars().all()
        
        return [
            {
                "id": str(doc.id),
                "filename": doc.original_filename,
                "file_type": doc.file_type,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at.isoformat()
            }
            for doc in documents
        ] 