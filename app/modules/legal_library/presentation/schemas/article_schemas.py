from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class ArticleCreateRequest(BaseModel):
    materia_juridica: str = Field(..., description="Ej. 'Penal', 'Civil', 'Laboral'")
    ley_o_codigo: str = Field(..., description="Ej. 'Código Civil Federal'")
    libro_o_titulo: Optional[str] = Field(None, description="Ej. 'Título Primero'")
    numero_articulo: str = Field(..., description="Ej. 'Art. 343'")
    cuerpo_texto: str = Field(..., description="El texto puro de la ley. Esto se usará para el embedding.")
    archivo_json_url: HttpUrl = Field(..., description="URL al archivo original en tu bucket/almacenamiento")

class ArticleResponse(BaseModel):
    id: int
    materia_juridica: str
    ley_o_codigo: str
    libro_o_titulo: Optional[str]
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    
    class Config:
        from_attributes = True
