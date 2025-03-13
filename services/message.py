from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import make_url
from models.message import Message, MessageRole
from models.embedding import Embedding
from models.conversation import Conversation
from models.user import User
from llama_index.core import VectorStoreIndex, ServiceContext, Document
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import openai
import os
from datetime import datetime
import uuid

class MessageService:
    def __init__(self, db: Session):
        self.db = db
        
        
    def get_conversation_messages(self, conversation: Conversation, limit: int = 10) -> List[Message]:
        """Get all messages in a conversation ordered by creation time"""
        return self.db.query(Message)\
            .filter(Message.conversation_id == conversation.id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()


    def create_message(
        self, 
        user: User, 
        conversation: Conversation, 
        content: str, 
        role: MessageRole, 
        source_embedding_id: Optional[uuid.UUID] = None) -> Message:
        """Create a new message"""
        message = Message(
            user_id=user.id,
            conversation_id=conversation.id,
            content=content,
            role=role,
            source_embedding_id=source_embedding_id
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_one_message(self, message_id: uuid.UUID) -> Message:
        return self.db.query(Message)\
            .filter(Message.id == message_id)\
            .first()
