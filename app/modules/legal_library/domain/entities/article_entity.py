from dataclasses import dataclass
from typing import Optional


@dataclass
class ArticleEntity:
    """
    Entidad pura de dominio.
    No conoce de FastAPI, Pydantic, SQLAlchemy ni bases de datos.
    Contiene únicamente las reglas y atributos del negocio.
    """

    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    document_id: Optional[int] = None
    libro_o_titulo: Optional[str] = None
    id: Optional[int] = None
    embedding: Optional[list[float]] = None
    similitud: Optional[float] = None
