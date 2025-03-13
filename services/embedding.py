from typing import List, Optional
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.text_splitter import SentenceSplitter
from llama_index.core.schema import TextNode
from sqlalchemy.orm import Session
import logging
import uuid
from models.embedding import Embedding
from models.item import Item
from services.item import ItemService

class EmbeddingService:
    def __init__(self, 
        db: Session, 
        openai_api_key: Optional[str] = None, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200
    ):
        """
        Initialize the embedding service.
        
        Args:
            openai_api_key (str): OpenAI API key for embeddings
            chunk_size (int): Size of text chunks in tokens
            chunk_overlap (int): Number of overlapping tokens between chunks
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.embed_model = OpenAIEmbedding(api_key=openai_api_key) if openai_api_key else None 
        self.text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.db = db
        self.item_service = ItemService(db)
        
    def get_conversation_embeddings(self, conversation_id: uuid.UUID) -> List[Embedding]:
        """
        Get all embeddings for a conversation.
        """
        return self.db \
            .query(Embedding) \
            .filter(
                Embedding.conversation_id == conversation_id,
                Embedding.item.has(Item.active)
            ).all()
    
    def get_embedding(self, embedding_id: uuid.UUID) -> Embedding:
        """
        Get an embedding by ID.
        """
        return self.db.query(Embedding).get({'id': embedding_id})
    
    def parse_embeddings_to_nodes(self, embeddings: List[Embedding]) -> List[TextNode]:
        """
        Parse embeddings to nodes.
        """
        nodes: List[TextNode] = []
        item = self.item_service.get_item_by_id_only(embeddings[0].item_id)
        for embedding in embeddings:
            nodes.append(
                TextNode(
                    id=embedding.id,
                    text=embedding.chunk_text,
                    embedding=embedding.embedding,
                    metadata={
                        "id": str(embedding.id),
                        "item_id": str(item.id),
                        "item_uri": item.uri,
                        "item_name": item.file_name,
                        'page': embedding.page,
                    }
                )
            )
        return nodes
