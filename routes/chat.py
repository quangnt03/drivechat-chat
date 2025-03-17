from fastapi import APIRouter, Depends, HTTPException
import uuid
import os
from dependencies.database import DatabaseService
from dependencies.security import validate_token
from services.message import MessageService, MessageRole
from services.conversation import ConversationService
from services.embedding import EmbeddingService
from services.item import ItemService
from services.chat import ChatService
from services.user import UserService
from schemas.chat import ChatRequest

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"]
)
db_service = DatabaseService(os.getenv('DATABASE_URL'))

@router.post("")
def chat(
    request: ChatRequest,
    user: dict = Depends(validate_token),
    message_service: MessageService = Depends(db_service.get_message_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service),
    user_service: UserService = Depends(db_service.get_user_service),
    chat_service: ChatService = Depends(db_service.get_chat_service)
):
    """
    Chat endpoint that supports RAG functionality within conversation context
    """
    # Extract user email from token
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conversation = conversation_service.get_conversation(
        conversation_id=request.conversation_id,
        user_id=user.id
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    message_service.create_message(
        user=user,
        conversation=conversation,
        content=request.message,
        role=MessageRole.USER
    )
    messages = message_service.get_conversation_messages(conversation)
    
    
    chat_msgs, chat_history = chat_service.parse_message_history(messages)
    
    
    answer_nodes = chat_service.get_answer_nodes(
        request.message, 
        conversation=conversation,
        chat_store=chat_history,
        messages=chat_msgs
    )
    sources_id = None
    sources = answer_nodes.sources
    if len(sources) and len(sources[0].raw_output.source_nodes):
        sources_id = uuid.UUID(
            sources[0].raw_output.source_nodes[0].node.extra_info['id']
        )
    message_service.create_message(
        user=user,
        conversation=conversation,
        role=MessageRole.ASSISTANT,
        content=answer_nodes.response,
        source_embedding_id=sources_id
    )
    return answer_nodes


@router.get("/history/{conversation_id}")
def get_chat_history(
    conversation_id: uuid.UUID,
    user: dict = Depends(validate_token),
    message_service: MessageService = Depends(db_service.get_message_service),
    limit: int = 5,
    conversation_service: ConversationService = Depends(db_service.get_conversation_service),
    user_service: UserService = Depends(db_service.get_user_service)
):
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conversation = conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=user.id
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = message_service.get_conversation_messages(conversation, limit=limit)
    return messages


@router.get("/history/{conversation_id}/{message_id}")
def get_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    user: dict = Depends(validate_token),
    message_service: MessageService = Depends(db_service.get_message_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service),
    embedding_service: EmbeddingService = Depends(db_service.get_embedding_service),
    user_service: UserService = Depends(db_service.get_user_service),
    item_service: ItemService = Depends(db_service.get_item_service)
):
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conversation = conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=user.id
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    message = message_service.get_one_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.source_embedding_id:
        source_embedding = embedding_service.get_embedding(message.source_embedding_id)
        item = item_service.get_item_by_id_only(source_embedding.item_id)
        return {
            **message.asdict(),
            "original_text": source_embedding.chunk_text,
            "page": source_embedding.page,
            "file_name": item.file_name,
            "uri": item.uri,
            "last_updated": item.last_updated
        }
    return message
