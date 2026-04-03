import logging
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger("app.share.infrastructure.services.embedding_service")


class EmbeddingEngine:
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None

        if settings.PARSING_ONLY_MODE or settings.USE_ZERO_EMBEDDINGS:
            logger.warning(
                "Embedding en modo parsing-only: se usarán vectores en cero de dimensión %s",
                settings.ZERO_EMBEDDING_DIM,
            )
            return

        logger.info(
            "Inicializando motor de embeddings de OpenAI: %s",
            settings.EMBEDDING_MODEL_NAME,
        )
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Genera un vector semántico usando la API de OpenAI.
        """
        if settings.PARSING_ONLY_MODE or settings.USE_ZERO_EMBEDDINGS:
            return [0.0] * settings.ZERO_EMBEDDING_DIM

        if self.client is None:
            raise RuntimeError(
                "OpenAI client no inicializado y modo zero embeddings desactivado"
            )

        try:
            normalized_text = self._normalize_text(text)
            response = await self.client.embeddings.create(
                input=[normalized_text], model=settings.EMBEDDING_MODEL_NAME
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generando embedding con OpenAI: {e}")
            raise

    def _normalize_text(self, text: str) -> str:
        normalized = text.replace("\n", " ").replace("\t", " ").strip()
        normalized = " ".join(normalized.split())

        if len(normalized) <= settings.MAX_EMBEDDING_CHARS:
            return normalized

        logger.warning(
            "Texto de embedding recortado de %s a %s caracteres",
            len(normalized),
            settings.MAX_EMBEDDING_CHARS,
        )
        return normalized[: settings.MAX_EMBEDDING_CHARS]


# Instancia global estática.
engine = EmbeddingEngine()
