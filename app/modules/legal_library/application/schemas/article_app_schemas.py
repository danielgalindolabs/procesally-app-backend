from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentAppInputDTO:
    titulo: str
    nombre_archivo: str
    url_oficial: str
    url_interna: Optional[str] = None
    fecha_publicacion: Optional[str] = None
    fecha_ultima_reforma: Optional[str] = None


@dataclass
class ArticleAppInputDTO:
    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    document_id: Optional[int] = None
    libro_o_titulo: Optional[str] = None


@dataclass
class ArticleAppOutputDTO:
    id: int
    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    document_id: Optional[int] = None
    libro_o_titulo: Optional[str] = None
    similitud: Optional[float] = None


@dataclass
class DeleteFileAppInputDTO:
    archivo_json_url: str


@dataclass
class BulkUrlIngestAppInputDTO:
    """DTO para la entrada de carga masiva por URL."""

    # Un diccionario de { "Título": { "url": "...", "fecha_pub": "...", "fecha_ref": "..." } }
    urls: dict[str, dict[str, str]]


@dataclass
class DiscoverLawsAppInputDTO:
    """DTO para solicitar el descubrimiento de leyes desde una URL índice."""

    index_url: str


@dataclass
class DiscoverLawsAppOutputDTO:
    """DTO de salida tras el descubrimiento de leyes."""

    total_found: int
    urls: dict[str, str]
