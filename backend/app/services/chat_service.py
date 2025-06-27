import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc

from ..models.chat import Conversation, Message, ConversationStatus
from ..models.user import User
from ..models.brand import Brand
from ..models.content import ContentProject

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for managing conversations and messages.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(
        self,
        user_id: UUID,
        title: str,
        function_type: str = "general",
        brand_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        model_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        reference: str = "ryb",
        api_key: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            function_type=function_type,
            brand_id=brand_id,
            project_id=project_id,
            model_provider=model_provider,
            model_name=model_name,
            reference=reference,
            api_key=api_key
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def get_user_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """Get conversations for a user."""
        query = select(Conversation).where(
            Conversation.user_id == user_id
        ).order_by(desc(Conversation.updated_at))
        
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def get_conversation_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_conversation_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a conversation."""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
        
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def save_message(
        self,
        conversation_id: UUID,
        content: str,
        is_user: bool,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Save a message to the database."""
        message = Message(
            conversation_id=conversation_id,
            user_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: Get from context
            content=content,
            is_user=is_user,
            meta_data=meta_data or {}
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message

    # MVP: Alias for add_message to match chat router expectations
    def add_message(
        self,
        conversation_id: UUID,
        content: str,
        is_user: bool,
        meta_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to the database - MVP version."""
        return self.save_message(conversation_id, content, is_user, meta_data)
    
    def update_conversation_title(self, conversation_id: UUID, title: str) -> bool:
        """Update conversation title."""
        try:
            conversation = self.get_conversation_by_id(conversation_id)
            if conversation:
                conversation.title = title
                conversation.updated_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return False
    
    def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete a conversation."""
        try:
            conversation = self.get_conversation_by_id(conversation_id)
            if conversation:
                self.db.delete(conversation)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False
    
    def generate_conversation_title(
        self,
        function_type: str,
        brand_name: Optional[str] = None
    ) -> str:
        """Generate a title for a conversation."""
        if function_type == "redacao":
            base = "Redação CPG"
        elif function_type == "oraculo":
            base = "Oráculo CPG"
        else:
            base = "Chat CPG"
        
        if brand_name:
            return f"{base} - {brand_name}"
        else:
            return f"{base} - {datetime.now().strftime('%d/%m/%Y %H:%M')}" 