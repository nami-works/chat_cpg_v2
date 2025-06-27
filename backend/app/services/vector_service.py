import os
import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import openai
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.knowledge import DocumentChunk, SearchQuery
from ..core.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        # Initialize OpenAI
        openai.api_key = settings.OPENAI_API_KEY
        
        # Initialize Pinecone
        self.pinecone_initialized = False
        self.index = None
        self.pc = None
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone connection."""
        try:
            if not settings.PINECONE_API_KEY:
                logger.warning("Pinecone API key not configured. Vector search will be disabled.")
                return
            
            # Initialize Pinecone with new API
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists, create if it doesn't
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            if settings.PINECONE_INDEX_NAME not in existing_indexes:
                logger.info(f"Creating Pinecone index: {settings.PINECONE_INDEX_NAME}")
                self.pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=1536,  # OpenAI ada-002 embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT or "us-west-2"
                    )
                )
            
            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            self.pinecone_initialized = True
            logger.info("Pinecone initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            self.pinecone_initialized = False
    
    async def create_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        Create embedding for text using OpenAI.
        """
        try:
            response = await openai.Embedding.acreate(
                model=model,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise ValueError(f"Embedding creation failed: {str(e)}")
    
    async def embed_document_chunks(
        self, 
        document_id: str, 
        user_id: str, 
        db: AsyncSession
    ) -> bool:
        """
        Create embeddings for all chunks of a document.
        """
        if not self.pinecone_initialized:
            logger.warning("Pinecone not initialized. Skipping embedding creation.")
            return False
        
        try:
            # Get all chunks for the document
            result = await db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.document_id == uuid.UUID(document_id),
                    DocumentChunk.user_id == uuid.UUID(user_id)
                ).order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()
            
            if not chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return False
            
            # Process chunks in batches
            batch_size = 10
            successful_embeddings = 0
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # Create embeddings for batch
                embedding_tasks = []
                for chunk in batch:
                    if not chunk.vector_id:  # Skip if already embedded
                        embedding_tasks.append(self._embed_chunk(chunk, db))
                
                # Wait for all embeddings in batch
                batch_results = await asyncio.gather(*embedding_tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch embedding error: {result}")
                    elif result:
                        successful_embeddings += 1
            
            logger.info(f"Successfully embedded {successful_embeddings} chunks for document {document_id}")
            return successful_embeddings > 0
            
        except Exception as e:
            logger.error(f"Failed to embed document chunks: {e}")
            return False
    
    async def _embed_chunk(self, chunk: DocumentChunk, db: AsyncSession) -> bool:
        """
        Create embedding for a single chunk.
        """
        try:
            # Create embedding
            embedding = await self.create_embedding(chunk.content)
            
            # Generate vector ID
            vector_id = f"{chunk.user_id}_{chunk.document_id}_{chunk.id}"
            
            # Prepare metadata for Pinecone
            metadata = {
                "user_id": str(chunk.user_id),
                "document_id": str(chunk.document_id),
                "knowledge_base_id": str(chunk.knowledge_base_id),
                "chunk_id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "content_length": chunk.content_length,
                "content_preview": chunk.content[:200],  # First 200 chars for preview
            }
            
            # Add to Pinecone
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)]
            )
            
            # Update chunk with vector info
            await db.execute(
                update(DocumentChunk)
                .where(DocumentChunk.id == chunk.id)
                .values(
                    vector_id=vector_id,
                    embedding_model="text-embedding-ada-002",
                    embedding_created_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed chunk {chunk.id}: {e}")
            return False
    
    async def search_similar_content(
        self,
        query: str,
        user_id: str,
        knowledge_base_id: Optional[str] = None,
        top_k: int = 10,
        score_threshold: float = 0.7,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using vector similarity.
        """
        if not self.pinecone_initialized:
            logger.warning("Pinecone not initialized. Vector search unavailable.")
            return []
        
        start_time = datetime.utcnow()
        
        try:
            # Create query embedding
            query_embedding = await self.create_embedding(query)
            
            # Prepare filter
            filter_dict = {"user_id": user_id}
            if knowledge_base_id:
                filter_dict["knowledge_base_id"] = knowledge_base_id
            
            # Search in Pinecone
            search_response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Process results
            results = []
            for match in search_response.matches:
                if match.score >= score_threshold:
                    results.append({
                        "chunk_id": match.metadata.get("chunk_id"),
                        "document_id": match.metadata.get("document_id"),
                        "knowledge_base_id": match.metadata.get("knowledge_base_id"),
                        "content_preview": match.metadata.get("content_preview"),
                        "score": match.score,
                        "chunk_index": match.metadata.get("chunk_index"),
                        "content_length": match.metadata.get("content_length")
                    })
            
            # Log search query if database session provided
            if db:
                await self._log_search_query(
                    query, user_id, knowledge_base_id, results, 
                    start_time, db
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _log_search_query(
        self,
        query: str,
        user_id: str,
        knowledge_base_id: Optional[str],
        results: List[Dict],
        start_time: datetime,
        db: AsyncSession
    ):
        """
        Log search query for analytics.
        """
        try:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            top_score = max([r["score"] for r in results]) if results else None
            
            search_query = SearchQuery(
                user_id=uuid.UUID(user_id),
                knowledge_base_id=uuid.UUID(knowledge_base_id) if knowledge_base_id else None,
                query_text=query,
                results_count=len(results),
                top_score=top_score,
                search_duration_ms=duration_ms
            )
            
            db.add(search_query)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log search query: {e}")
    
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
        try:
            result = await db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.id == uuid.UUID(chunk_id),
                    DocumentChunk.user_id == uuid.UUID(user_id)
                )
            )
            chunk = result.scalar_one_or_none()
            
            if not chunk:
                return None
            
            content_data = {
                "id": str(chunk.id),
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "content_length": chunk.content_length,
                "document_id": str(chunk.document_id),
                "knowledge_base_id": str(chunk.knowledge_base_id),
                "page_number": chunk.page_number,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "metadata": chunk.meta,
                "created_at": chunk.created_at.isoformat()
            }
            
            if include_context:
                content_data.update({
                    "context_before": chunk.context_before,
                    "context_after": chunk.context_after
                })
            
            return content_data
            
        except Exception as e:
            logger.error(f"Failed to get chunk content: {e}")
            return None
    
    async def delete_document_vectors(
        self,
        document_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Delete all vectors for a document from Pinecone.
        """
        if not self.pinecone_initialized:
            return True  # Consider it successful if Pinecone is not available
        
        try:
            # Get all chunk vector IDs for the document
            result = await db.execute(
                select(DocumentChunk.vector_id).where(
                    DocumentChunk.document_id == uuid.UUID(document_id),
                    DocumentChunk.user_id == uuid.UUID(user_id),
                    DocumentChunk.vector_id.isnot(None)
                )
            )
            vector_ids = [row[0] for row in result.fetchall()]
            
            if vector_ids:
                # Delete from Pinecone
                self.index.delete(ids=vector_ids)
                logger.info(f"Deleted {len(vector_ids)} vectors for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document vectors: {e}")
            return False
    
    async def get_vector_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get vector statistics for a user.
        """
        if not self.pinecone_initialized:
            return {"total_vectors": 0, "status": "unavailable"}
        
        try:
            # Get index stats
            stats = self.index.describe_index_stats()
            
            # Query user-specific stats (approximate)
            user_query = self.index.query(
                vector=[0.0] * 1536,  # Dummy vector
                top_k=1,
                include_metadata=True,
                filter={"user_id": user_id}
            )
            
            return {
                "total_vectors": stats.total_vector_count,
                "user_vectors": len(user_query.matches) if user_query.matches else 0,
                "dimension": stats.dimension,
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to get vector stats: {e}")
            return {"total_vectors": 0, "status": "error", "error": str(e)}
    
    async def update_chunk_embedding(
        self,
        chunk_id: str,
        user_id: str,
        new_content: str,
        db: AsyncSession
    ) -> bool:
        """
        Update embedding for a chunk with new content.
        """
        if not self.pinecone_initialized:
            return False
        
        try:
            # Get the chunk
            result = await db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.id == uuid.UUID(chunk_id),
                    DocumentChunk.user_id == uuid.UUID(user_id)
                )
            )
            chunk = result.scalar_one_or_none()
            
            if not chunk:
                return False
            
            # Create new embedding
            new_embedding = await self.create_embedding(new_content)
            
            # Update in Pinecone
            vector_id = chunk.vector_id or f"{user_id}_{chunk.document_id}_{chunk_id}"
            
            metadata = {
                "user_id": str(user_id),
                "document_id": str(chunk.document_id),
                "knowledge_base_id": str(chunk.knowledge_base_id),
                "chunk_id": str(chunk_id),
                "chunk_index": chunk.chunk_index,
                "content_length": len(new_content),
                "content_preview": new_content[:200],
            }
            
            self.index.upsert(
                vectors=[(vector_id, new_embedding, metadata)]
            )
            
            # Update chunk in database
            await db.execute(
                update(DocumentChunk)
                .where(DocumentChunk.id == uuid.UUID(chunk_id))
                .values(
                    content=new_content,
                    content_length=len(new_content),
                    vector_id=vector_id,
                    embedding_created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update chunk embedding: {e}")
            return False 