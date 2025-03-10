import os 
from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from dependencies.security import validate_token
from dependencies.database import DatabaseService, UserService, ConversationService, ItemService
from schemas.conversation import ConversationCreate

router = APIRouter(prefix='/api/v1/conversation', tags=['Conversations'])
db_service = DatabaseService(os.getenv('DATABASE_URL'))


@router.post("")
def create_conversation(
    conversation: ConversationCreate,
    user: dict = Depends(validate_token),
    user_service: UserService = Depends(db_service.get_user_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service)
):
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        user = user_service.create_user(email)
    conversation = conversation_service.create_conversation(user.id, conversation)
    
    return conversation


@router.get("")
def get_all_conversation(
    title: str = None,
    user: dict = Depends(validate_token),
    user_service: UserService = Depends(db_service.get_user_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service)
):
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if title:
        conversation = conversation_service.get_user_conversations_by_title(user.id, title)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = conversation_service.get_user_conversations(user.id)
    return conversation


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: UUID4,
    user: dict = Depends(validate_token),
    user_service: UserService = Depends(db_service.get_user_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service)
):
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conversation = conversation_service.get_conversation(conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.put("/{conversation_id}")
def update_conversation(
    conversation_id: UUID4,
    data: ConversationCreate,
    user: dict = Depends(validate_token),
    user_service: UserService = Depends(db_service.get_user_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service)
):
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conversation = conversation_service.get_conversation(conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    new_conversation = conversation_service.update_conversation(conversation, data)
    return new_conversation


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: UUID4,
    user: dict = Depends(validate_token),
    user_service: UserService = Depends(db_service.get_user_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service),
    item_service: ItemService = Depends(db_service.get_item_service)
):
    email = user['UserAttributes'][0]['Value']
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conversation = conversation_service.get_conversation(conversation_id, user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    items = item_service.get_items_by_conversation(conversation, active_only=False)
    if len(items) > 0:
        raise HTTPException(status_code=400, detail="Conversation has items")
    conversation_service.delete_conversation(conversation)
    return {
        "message": "Conversation deleted successfully",
        'id': conversation_id
    }