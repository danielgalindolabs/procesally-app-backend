from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Toma un texto y devuelve un vector semántico (lista de floats)"""
        pass
