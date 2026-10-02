import logging
from typing import List, Optional
from fastembed import TextEmbedding
from app.core.config import settings

logger = logging.getLogger(__name__)

_embedding_model: Optional[TextEmbedding] = None

def get_embedding_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        model_name = settings.EMBEDDING_MODEL or "BAAI/bge-small-en-v1.5"
        _embedding_model = TextEmbedding(model_name=model_name)
    return _embedding_model

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of strings using FastEmbed.
    Returns a list of vectors (each vector is a list of floats).
    """
    if not texts:
        return []
    try:
        model = get_embedding_model()
        embeddings_generator = model.embed(texts)
        return [embedding.tolist() for embedding in embeddings_generator]
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return []

