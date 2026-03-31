from app.modules.legal_library.domain.services.embedding_service import \
    EmbeddingService
from app.share.infrastructure.services.embedding_service import engine


class OpenAIEmbeddingService(EmbeddingService):
    """
    Implementación en Infraestructura del contrato de Generación de Embeddings.
    Fija al cliente global compartido de OpenAI de nuestra app principal.
    """

    async def generate_embedding(self, text: str) -> list[float]:
        # Delega el trabajo real al engine de OpenAI en share
        return await engine.generate_embedding(text)
