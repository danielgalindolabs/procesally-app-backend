from typing import List

from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.share.infrastructure.services.embedding_service import engine


class OpenAIEmbeddingService(EmbeddingService):
    async def generate_embedding(self, text: str) -> List[float]:
        return await engine.generate_embedding(text)
