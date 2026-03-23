from sqlmodel import SQLModel, Field
from sqlalchemy import Column, UniqueConstraint
from pgvector.sqlalchemy import Vector
from typing import Optional

class LegalArticle(SQLModel, table=True):
    __tablename__ = "legal_articles"
    # Evitar duplicados exactos: No pueden haber dos "Art. 1" en el mismo "Código Penal"
    __table_args__ = (
        UniqueConstraint("ley_o_codigo", "numero_articulo", name="uq_ley_articulo"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    materia_juridica: str = Field(description="Ej. 'Penal', 'Civil', 'Laboral'")
    ley_o_codigo: str = Field(description="Ej. 'Código Civil Federal', 'Ley Federal del Trabajo'")
    libro_o_titulo: Optional[str] = Field(default=None, description="Agrupación superior. Ej. 'Título Primero'")
    numero_articulo: str = Field(description="Ej. 'Art. 343', '12'")
    
    cuerpo_texto: str = Field(description="El texto puro de la ley o jurisprudencia para vectorizar")
    archivo_json_url: str = Field(description="URL al bucket (S3/Cloud) donde vive el JSON original crudo")
    
    # El vector semántico calculado por OpenAI (text-embedding-3-small = 1536 dims)
    embedding: list[float] | None = Field(
        default=None, 
        sa_column=Column(Vector(1536))
    )

