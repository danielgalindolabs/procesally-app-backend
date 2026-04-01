import datetime
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, SQLModel


class LegalDocument(SQLModel, table=True):
    __tablename__ = "legal_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str = Field(description="Nombre de la ley, libro o boletín")
    nombre_archivo: str = Field(description="Nombre original del archivo cargado")
    url_oficial: str = Field(description="URL al sitio oficial (ej. DOF)")
    url_interna: Optional[str] = Field(
        default=None, description="URL interna en nuestro storage (S3/local)"
    )
    fecha_publicacion: Optional[str] = Field(
        default=None, description="Fecha de publicación original"
    )
    fecha_ultima_reforma: Optional[str] = Field(
        default=None, description="Fecha de la última reforma reportada"
    )
    fecha_carga: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        description="Fecha y hora de registro en el sistema",
    )
    materias_juridicas: Optional[str] = Field(
        default=None,
        description="Materias jurídicas separadas por coma. Ej: 'Civil, Laboral, Mercantil'",
    )


class LegalArticle(SQLModel, table=True):
    __tablename__ = "legal_articles"

    id: Optional[int] = Field(default=None, primary_key=True)

    document_id: Optional[int] = Field(
        default=None, foreign_key="legal_documents.id", index=True
    )

    materia_juridica: str = Field(
        description="Materias jurídicas separadas por coma. Ej: 'Civil, Laboral'"
    )
    ley_o_codigo: str = Field(
        description="Ej. 'Código Civil Federal', 'Ley Federal del Trabajo'"
    )
    libro_o_titulo: Optional[str] = Field(
        default=None, description="Agrupación superior. Ej. 'Título Primero'"
    )
    numero_articulo: str = Field(description="Ej. 'Art. 343', '12'")

    cuerpo_texto: str = Field(
        description="El texto puro de la ley o jurisprudencia para vectorizar"
    )
    archivo_json_url: str = Field(
        description="URL al bucket (S3/Cloud) donde vive el JSON original crudo"
    )

    embedding: Optional[List[float]] = Field(
        default=None, sa_column=Column(Vector(1536))
    )
