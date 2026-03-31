from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ArticleCreateRequest(BaseModel):
    materia_juridica: str = Field(..., description="Ej. 'Penal', 'Civil', 'Laboral'")
    ley_o_codigo: str = Field(..., description="Ej. 'Código Civil Federal'")
    libro_o_titulo: Optional[str] = Field(None, description="Ej. 'Título Primero'")
    numero_articulo: str = Field(..., description="Ej. 'Art. 343'")
    cuerpo_texto: str = Field(
        ..., description="El texto puro de la ley. Esto se usará para el embedding."
    )
    archivo_json_url: HttpUrl = Field(
        ..., description="URL al archivo original en tu bucket/almacenamiento"
    )
    fecha_publicacion: Optional[str] = Field(None, description="Ej. '18-01-1952'")
    fecha_ultima_reforma: Optional[str] = Field(None, description="Ej. '03-01-1979'")


class ArticleResponse(BaseModel):
    id: int
    materia_juridica: str
    ley_o_codigo: str
    libro_o_titulo: Optional[str]
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    document_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SearchRequest(BaseModel):
    consulta: str = Field(
        ..., description="Texto en lenguaje natural para buscar artículos similares"
    )
    limite: Optional[int] = Field(None, ge=1, le=50, description="Cantidad máxima opcional de resultados")
    materia_juridica: Optional[str] = Field(
        None, description="Filtro opcional por materia (ej. 'Civil', 'Laboral')"
    )
    ley_o_codigo: Optional[str] = Field(
        None,
        description="Filtro opcional por ley específica (ej. 'Código Civil Federal')",
    )


class SearchResult(ArticleResponse):
    similitud: float = Field(
        ..., description="Puntuación de similitud coseno (0 a 1, donde 1 es idéntico)"
    )


class DocumentMetadataInfo(BaseModel):
    id: str
    fecha_de_publicacion: str
    fecha_de_ultima_reforma: str


class BulkUrlIngestRequest(BaseModel):
    # Diccionario de { "Nombre de la Ley": DocumentMetadataInfo }
    urls: dict[str, DocumentMetadataInfo] = Field(
        ...,
        description="Diccionario de títulos y metadatos (URL, fechas) del documento",
    )


class ParseIndexResponse(BaseModel):
    documentos: dict[str, DocumentMetadataInfo]
