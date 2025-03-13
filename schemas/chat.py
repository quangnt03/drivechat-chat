from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import datetime
from models.message import MessageRole

class ChatMessage(BaseModel):
    content: str
    role: MessageRole

class ChatRequest(BaseModel):
    conversation_id: UUID4
    message: str
    use_rag: bool = True
    top_k: int = 3

class ChatResponse(BaseModel):
    conversation_id: UUID4
    message: str
    sources: List[dict] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistory(BaseModel):
    messages: List[ChatMessage]
    
    class Config:
        from_attributes = True
