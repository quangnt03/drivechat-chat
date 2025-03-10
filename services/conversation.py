from typing import Optional
from sqlalchemy.orm import Session
from models import Conversation
from models.schemas import ConversationCreate
from uuid import UUID
import logging
from datetime import datetime

class ConversationService:
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_conversation(self, user_id: UUID, data: ConversationCreate) -> Optional[Conversation]:
        """
        Create a new conversation.
        
        Args:
            user_id (UUID): ID of the user creating the conversation
            data (ConversationCreate): Conversation data
            
        Returns:
            Optional[Conversation]: Created conversation or None if failed
        """
        try:
            conversation = Conversation(
                user_id=user_id,
                title=data.title,
                context=data.context,
                updated_at=datetime.now()
            )
            self.session.add(conversation)
            self.session.commit()
            self.session.refresh(conversation)
            
            self.logger.info(f"Created conversation: {conversation.id}")
            return conversation
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to create conversation: {str(e)}")
            return None

    def get_user_conversations(self, user_id: UUID) -> list[Conversation]:
        """
        Get all conversations for a user.
        
        Args:
            user_id (UUID): User ID
            
        Returns:
            list[Conversation]: List of conversations
        """
        return self.session.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .order_by(Conversation.created_at.desc())\
            .all()

    def get_conversation(self, conversation_id: UUID, user_id: UUID) -> Optional[Conversation]:
        """
        Get a specific conversation.
        
        Args:
            conversation_id (UUID): Conversation ID
            user_id (UUID): User ID for verification
            
        Returns:
            Optional[Conversation]: Conversation if found and owned by user, None otherwise
        """
        return self.session.query(Conversation)\
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first() 
            
    def get_user_conversations_by_title(self, user_id: UUID, title: str) -> list[Conversation]:
        """
        Get conversations by title for a user.
        
        Args:
            user_id (UUID): User ID
            title (str): Title of the conversation
            
        Returns:
            list[Conversation]: List of conversations
        """
        return self.session.query(Conversation)\
            .filter(
                Conversation.user_id == user_id,
                Conversation.title.ilike(f"%{title}%")
            )\
            .order_by(Conversation.created_at.desc())\
            .all()
            
        
    def update_conversation(self, conversation: Conversation, data: ConversationCreate) -> Optional[Conversation]:
        """
        Update a conversation.
        
        Args:
            conversation (Conversation): Conversation to update
            data (ConversationCreate): Updated conversation data
            
        Returns:
            Optional[Conversation]: Updated conversation or None if failed
        """
        try:
            conversation.title = data.title
            conversation.context = data.context
            conversation.updated_at = datetime.now()
            self.session.commit()
            self.session.refresh(conversation)
            
            self.logger.info(f"Updated conversation: {conversation.id}")
            return conversation
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to update conversation: {str(e)}")
            return None
    
    
    def delete_conversation(self, conversation: Conversation) -> None:
        """
        Delete a conversation.
        
        Args:
            conversation (Conversation): Conversation to delete
        """
        try:
            self.session.delete(conversation)
            self.session.commit()
            self.logger.info(f"Deleted conversation: {conversation.id}")
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to delete conversation: {str(e)}")