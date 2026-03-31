from abc import ABC, abstractmethod
from typing import Optional

from app.modules.legal_library.domain.entities.article_entity import \
    ArticleEntity
from app.modules.legal_library.domain.entities.legal_document_entity import \
    LegalDocumentEntity


class LegalRepository(ABC):
    @abstractmethod
    async def create_document(
        self, document: LegalDocumentEntity
    ) -> LegalDocumentEntity:
        """Registra un nuevo documento legal de origen en el repositorio."""
        pass

    @abstractmethod
    async def create_article(self, article: ArticleEntity) -> Optional[ArticleEntity]:
        """Guarda un artículo y devuelve la entidad completa."""
        pass

    @abstractmethod
    async def get_article_by_id(self, article_id: int) -> Optional[ArticleEntity]:
        """Obtiene un artículo por su ID."""
        pass

    @abstractmethod
    async def get_articles_by_numbers(
        self, numbers: list[str], ley: str
    ) -> list[ArticleEntity]:
        """Obtiene varios artículos por sus números y ley."""
        pass

    @abstractmethod
    async def search_similar_vectors(
        self,
        vector: list[float],
        limit: int = 5,
        materia_juridica: Optional[str] = None,
        ley_o_codigo: Optional[str] = None,
    ) -> list[ArticleEntity]:
        """Busca artículos que sean similares a un vector dado y devuelve una lista de entidades."""
        pass

    @abstractmethod
    async def delete_articles_by_file(self, file_url: str) -> int:
        """Elimina todos los artículos asociados a un archivo y retorna el conteo de eliminados."""
        pass

    @abstractmethod
    async def get_document_by_url(self, url: str) -> Optional[LegalDocumentEntity]:
        """Obtiene un documento por su URL oficial."""
        pass

    @abstractmethod
    async def get_document_by_title(self, title: str) -> Optional[LegalDocumentEntity]:
        """Obtiene un documento por su título."""
        pass

    @abstractmethod
    async def get_document_by_filename(self, filename: str) -> Optional[LegalDocumentEntity]:
        """Obtiene un documento por su nombre de archivo."""
        pass

    @abstractmethod
    async def delete_document(self, doc_id: int) -> bool:
        """Elimina un documento y todos sus artículos asociados."""
        pass
