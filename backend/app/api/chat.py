from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
# from langchain.memory import ConversationBufferMemory  # Commented for MVP

from app.db.database import get_db
from app.auth.security import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.brand import Brand
# from app.models.content import ContentProject  # Commented for MVP
from app.services.chat_service import ChatService
from app.services.ai_service import AIService
# from app.services.content_service import ContentService  # Commented for MVP
from app.services.brand_service import BrandService


class ChatMessage(BaseModel):
    content: str


class ChatResponse(BaseModel):
    content: str
    conversation_id: UUID
    message_id: UUID


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    function_type: str = "general"  # MVP: only general for now
    brand_id: Optional[UUID] = None
    # project_id: Optional[UUID] = None  # Commented for MVP
    model_provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    # reference: str = "ryb"  # Commented for MVP
    api_key: Optional[str] = None


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    function_type: str
    brand_id: Optional[UUID]
    # project_id: Optional[UUID]  # Commented for MVP
    model_provider: str
    model_name: str
    # reference: str  # Commented for MVP
    created_at: datetime
    updated_at: datetime
    message_count: int

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: UUID
    content: str
    is_user: bool
    created_at: datetime
    meta_data: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ChatContextResponse(BaseModel):
    # available_functions: List[str]  # Commented for MVP
    available_models: Dict[str, Dict[str, str]]
    # available_references: Dict[str, str]  # Commented for MVP
    brands: List[Dict[str, Any]]


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/context", response_model=ChatContextResponse)
async def get_chat_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available chat context options - MVP version"""
    ai_service = AIService()
    brand_service = BrandService(db)
    
    # Get available brands
    brands = brand_service.get_brands()
    brands_data = [
        {
            "id": str(brand.id),
            "name": brand.name,
            "slug": brand.slug
        }
        for brand in brands
    ]
    
    return ChatContextResponse(
        # available_functions=ai_service.get_available_functions(),  # Commented for MVP
        available_models=ai_service.get_available_models(),
        # available_references=ai_service.get_available_references(),  # Commented for MVP
        brands=brands_data
    )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation - MVP version"""
    chat_service = ChatService(db)
    
    # Validate brand if provided
    brand = None
    if conversation_data.brand_id:
        brand_service = BrandService(db)
        brand = brand_service.get_brand_by_id(conversation_data.brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
    
    # MVP: Comment out project validation
    # project = None
    # if conversation_data.project_id:
    #     content_service = ContentService(db)
    #     project = content_service.get_project_by_id(conversation_data.project_id)
    #     if not project or project.user_id != current_user.id:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="Project not found or not accessible"
    #         )
    
    # Generate title if not provided
    title = conversation_data.title or chat_service.generate_conversation_title(
        function_type=conversation_data.function_type,
        brand_name=brand.name if brand else None
    )
    
    conversation = chat_service.create_conversation(
        user_id=current_user.id,
        title=title,
        function_type=conversation_data.function_type,
        brand_id=conversation_data.brand_id,
        # project_id=conversation_data.project_id,  # Commented for MVP
        project_id=None,  # MVP: Always None
        model_provider=conversation_data.model_provider,
        model_name=conversation_data.model_name,
        # reference=conversation_data.reference,  # Commented for MVP
        reference="general",  # MVP: Always general
        api_key=conversation_data.api_key
    )
    
    # Add message count
    conversation.message_count = 0
    
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's conversations"""
    chat_service = ChatService(db)
    conversations = chat_service.get_user_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Add message counts
    for conv in conversations:
        conv.message_count = len(conv.messages)
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation"""
    chat_service = ChatService(db)
    conversation = chat_service.get_conversation_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Add message count
    conversation.message_count = len(conversation.messages)
    
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages from a conversation"""
    chat_service = ChatService(db)
    
    # Verify conversation belongs to user
    conversation = chat_service.get_conversation_by_id(conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = chat_service.get_conversation_messages(
        conversation_id=conversation_id,
        skip=skip,
        limit=limit
    )
    
    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: UUID,
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to a conversation - MVP version with simplified AI response"""
    chat_service = ChatService(db)
    
    # Verify conversation belongs to user
    conversation = chat_service.get_conversation_by_id(conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    try:
        # Save user message
        user_message = chat_service.add_message(
            conversation_id=conversation_id,
            content=message.content,
            is_user=True
        )
        
        # MVP: Simplified AI response logic
        ai_service = AIService()
        
        # Get brand context if available
        brand_context = ""
        if conversation.brand_id:
            brand_service = BrandService(db)
            brand = brand_service.get_brand_by_id(conversation.brand_id)
            if brand:
                brand_context = f"Brand: {brand.name}\n"
                if brand.brand_description:
                    brand_context += f"Description: {brand.brand_description}\n"
                if brand.products_info:
                    brand_context += f"Products: {brand.products_info}\n"
        
        # Generate AI response with brand context
        response_content = await ai_service.generate_simple_response(
            user_message=message.content,
            brand_context=brand_context,
            model_provider=conversation.model_provider,
            model_name=conversation.model_name,
            api_key=conversation.api_key
        )
        
        # Save AI response
        ai_message = chat_service.add_message(
            conversation_id=conversation_id,
            content=response_content,
            is_user=False
        )
        
        return ChatResponse(
            content=response_content,
            conversation_id=conversation_id,
            message_id=ai_message.id
        )
        
    except Exception as e:
        # MVP: Simple error handling
        error_response = f"Sorry, I encountered an error: {str(e)}"
        ai_message = chat_service.add_message(
            conversation_id=conversation_id,
            content=error_response,
            is_user=False
        )
        
        return ChatResponse(
            content=error_response,
            conversation_id=conversation_id,
            message_id=ai_message.id
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation"""
    chat_service = ChatService(db)
    
    # Verify conversation belongs to user
    conversation = chat_service.get_conversation_by_id(conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    success = chat_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )
    
    return {"message": "Conversation deleted successfully"}


@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: UUID,
    title: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update conversation title"""
    chat_service = ChatService(db)
    
    # Verify conversation belongs to user
    conversation = chat_service.get_conversation_by_id(conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    updated_conversation = chat_service.update_conversation_title(conversation_id, title)
    if not updated_conversation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation title"
        )
    
    return {"message": "Conversation title updated successfully"}


# MVP: Comment out advanced features
# @router.post("/conversations/{conversation_id}/feedback")
# async def submit_feedback(
#     conversation_id: UUID,
#     message_id: UUID,
#     feedback: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Submit feedback for a message"""
#     pass
#
# @router.get("/conversations/{conversation_id}/export")
# async def export_conversation(
#     conversation_id: UUID,
#     format: str = "markdown",
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Export conversation in various formats"""
#     pass 