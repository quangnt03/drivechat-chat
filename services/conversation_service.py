from typing import List, Optional
from sqlalchemy.orm import Session
from models.conversation import Conversation
from schemas.conversation import ConversationCreate, ConversationUpdate
from fastapi import HTTPException
import uuid

class ConversationService:
    @staticmethod
    def create_conversation(db: Session, conversation: ConversationCreate, user_id: uuid.UUID) -> Conversation:
        """Create a new conversation"""
        db_conversation = Conversation(
            title=conversation.title,
            user_id=user_id
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation

    @staticmethod
    def get_conversation(db: Session, conversation_id: uuid.UUID) -> Optional[Conversation]:
        """Get a specific conversation by ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def get_user_conversations(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations for a specific user"""
        return db.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .order_by(Conversation.updated_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def update_conversation(
        db: Session, 
        conversation_id: uuid.UUID, 
        conversation_update: ConversationUpdate,
        user_id: uuid.UUID
    ) -> Conversation:
        """Update a conversation"""
        db_conversation = ConversationService.get_conversation(db, conversation_id)
        if not db_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if db_conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this conversation")
        
        for field, value in conversation_update.dict(exclude_unset=True).items():
            setattr(db_conversation, field, value)
        
        db.commit()
        db.refresh(db_conversation)
        return db_conversation

    @staticmethod
    def delete_conversation(db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a conversation"""
        db_conversation = ConversationService.get_conversation(db, conversation_id)
        if not db_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if db_conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
        
        db.delete(db_conversation)
        db.commit()
        return True 