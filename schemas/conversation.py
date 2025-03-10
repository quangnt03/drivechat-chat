from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class ConversationBase(BaseModel):
    title: str
    context: str

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: Optional[str] = None

class Conversation(ConversationBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True