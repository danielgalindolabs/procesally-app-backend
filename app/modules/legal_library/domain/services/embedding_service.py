from abc import ABC, abstractmethod
from typing import List


class EmbeddingService(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Toma un texto y devuelve un vector semántico (lista de floats)"""
        pass
