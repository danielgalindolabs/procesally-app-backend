from openai import AsyncOpenAI
import logging
from app.core.config import settings

logger = logging.getLogger("app.share.infrastructure.services.embedding_service")

class EmbeddingEngine:
    def __init__(self):
        logger.info(f"Inicializando motor de embeddings de OpenAI: {settings.EMBEDDING_MODEL_NAME}")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Genera un vector semántico usando la API de OpenAI.
        """
        try:
            response = await self.client.embeddings.create(
                input=[text.replace("\n", " ")],
                model=settings.EMBEDDING_MODEL_NAME
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generando embedding con OpenAI: {e}")
            raise

# Instancia global estática.
engine = EmbeddingEngine()

