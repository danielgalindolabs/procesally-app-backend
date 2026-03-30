import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatasourceDocumentInputDTO:
    """Estructura de entrada para un documento legal"""

    titulo: str
    nombre_archivo: str
    url_oficial: str
    url_interna: Optional[str] = None


@dataclass
class DatasourceDocumentOutputDTO:
    """Estructura de salida para un documento legal"""

    id: int
    titulo: str
    nombre_archivo: str
    url_oficial: str
    fecha_carga: datetime.datetime
    url_interna: Optional[str] = None


@dataclass
class DatasourceArticleInputDTO:
    """Estructura mínima de entrada al Datasource"""

    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    document_id: Optional[int] = None
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
    document_id: Optional[int] = None
    libro_o_titulo: Optional[str] = None
    embedding: Optional[list[float]] = None
    similitud: Optional[float] = None


class LegalDatasource(ABC):
    @abstractmethod
    async def create_document(
        self, ds_input: DatasourceDocumentInputDTO
    ) -> DatasourceDocumentOutputDTO:
        """Registra un nuevo documento legal de origen."""
        pass

    @abstractmethod
    async def create_article(
        self, ds_input: DatasourceArticleInputDTO
    ) -> Optional[DatasourceArticleOutputDTO]:
        """Crea un artículo esperando un DTO de entrada e incluye el document_id si existe."""
        pass

    @abstractmethod
    async def get_article_by_id(
        self, article_id: int
    ) -> Optional[DatasourceArticleOutputDTO]:
        """Obtiene un artículo crudo de infraestructura por su ID."""
        pass

    @abstractmethod
    async def search_by_vector(
        self,
        vector: list[float],
        limit: int = 5,
        materia_juridica: Optional[str] = None,
        ley_o_codigo: Optional[str] = None,
    ) -> list[DatasourceArticleOutputDTO]:
        """Busca artículos que sean similares a un vector y devuelve DTOs de Datasource."""
        pass

    @abstractmethod
    async def delete_by_file(self, file_url: str) -> int:
        """Elimina artículos por el URL del archivo y retorna el conteo."""
        pass
