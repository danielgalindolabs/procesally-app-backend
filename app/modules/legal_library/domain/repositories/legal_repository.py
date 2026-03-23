from abc import ABC, abstractmethod

class LegalRepository(ABC):

    @abstractmethod
    async def get_article_by_id(self, article_id: int) -> dict:
        pass
        
    @abstractmethod
    async def search_similar_vectors(self, vector: list[float], limit: int = 5) -> list:
        pass
