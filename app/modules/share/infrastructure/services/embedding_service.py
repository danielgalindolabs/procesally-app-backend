import logging

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger("app.share.infrastructure.services.embedding_service")


class EmbeddingEngine:
    def __init__(self):
        logger.info(
            f"Inicializando motor de embeddings de OpenAI: {settings.EMBEDDING_MODEL_NAME}"
        )
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Genera un vector semántico usando la API de OpenAI.
        """
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
