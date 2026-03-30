from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatasourceArticleInputDTO:
    """Estructura mínima de entrada al Datasource"""

    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    libro_o_titulo: Optional[str] = None
    embedding: Optional[list[float]] = None


@dataclass
class DatasourceArticleOutputDTO:
    """Estructura mínima de salida del Datasource"""

    id: int
    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    libro_o_titulo: Optional[str] = None
    embedding: Optional[list[float]] = None
    similitud: Optional[float] = None


class LegalDatasource(ABC):
    @abstractmethod
    async def create_article(
        self, ds_input: DatasourceArticleInputDTO
    ) -> Optional[DatasourceArticleOutputDTO]:
        """Crea un artículo esperando un DTO de entrada y devuelve un DTO de salida."""
        pass

    @abstractmethod
    async def get_article_by_id(
        self, article_id: int
    ) -> Optional[DatasourceArticleOutputDTO]:
        """Obtiene un artículo crudo de infraestructura por su ID."""
        pass

    @abstractmethod
    async def search_by_vector(
        self, vector: list[float], limit: int = 5
    ) -> list[DatasourceArticleOutputDTO]:
        """Busca artículos que sean similares a un vector y devuelve DTOs de Datasource."""
        pass
