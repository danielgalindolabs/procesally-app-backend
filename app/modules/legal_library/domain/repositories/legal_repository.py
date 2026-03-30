from abc import ABC, abstractmethod
from typing import Optional

from app.modules.legal_library.domain.entities.article_entity import ArticleEntity


class LegalRepository(ABC):
    @abstractmethod
    async def create_article(self, article: ArticleEntity) -> Optional[ArticleEntity]:
        """Guarda un artículo y devuelve la entidad completa."""
        pass

    @abstractmethod
    async def get_article_by_id(self, article_id: int) -> Optional[ArticleEntity]:
        """Obtiene un artículo por su ID."""
        pass

    @abstractmethod
    async def search_similar_vectors(
        self, vector: list[float], limit: int = 5
    ) -> list[ArticleEntity]:
        """Busca artículos que sean similares a un vector dado y devuelve una lista de entidades."""
        pass

    @abstractmethod
    async def delete_articles_by_file(self, file_url: str) -> int:
        """Elimina todos los artículos asociados a un archivo y retorna el conteo de eliminados."""
        pass
