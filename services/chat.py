from typing import List, Dict, Optional, Union
from sqlalchemy.orm import Session
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.prompts import ChatMessage, MessageRole as ChatMessageRole
from models.conversation import Conversation
from models.message import Message, MessageRole
from services.embedding import EmbeddingService
import openai
import os
import uuid

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(
            db=db,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.llm = OpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.embed_model = self.embedding_service.embed_model
        self.chat_store = SimpleChatStore()
        

    def parse_message_history(self, messages: List[Message]) -> \
        Union[List[ChatMessage], Optional[SimpleChatStore]]:
        """Parse message history into a list of strings"""
        chat_messages: List[ChatMessage] = []
        for message in messages:
            role = str(message.role.value).lower()
            chat_message = ChatMessage(
                role=role,
                content=message.content,
                data={
                    'conversation_id': message.conversation_id,
                    'created_at': message.created_at,
                    'source': message.source_embedding_id
                }
            )
            chat_messages.append(chat_message)
            self.chat_store.add_message(str(message.id), message=chat_message)
        return (chat_messages, self.chat_store,)
    
        
    def get_answer_nodes(
        self, 
        query_text: str,
        conversation: Conversation,
        chat_store: Optional[SimpleChatStore],
        messages: List[Message],
        # top_k: int = 5,
        # use_hybrid: bool = True
    ):
        """
        Get relevant nodes using hybrid search within conversation context
        """
        embeddings = self.embedding_service.get_conversation_embeddings(conversation.id)
        if not len(embeddings):
            return None
        nodes = self.embedding_service.parse_embeddings_to_nodes(embeddings)
        
        self.vector_store = VectorStoreIndex(
            nodes=nodes,
            embed_model=self.embed_model,
        )
        chat_mem = ChatMemoryBuffer.from_defaults(
            token_limit=4096,
            chat_history=messages, 
            chat_store=chat_store,
            chat_store_key=str(conversation.id) 
        )
        chat_engine = self.vector_store.as_chat_engine(
            llm=self.llm,
            chat_history=messages,
            memory=chat_mem
        )
        
        response = chat_engine.chat(
            message=query_text,
            chat_history=messages,
        )
        return response
        
    