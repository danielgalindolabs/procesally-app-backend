from dataclasses import dataclass
from typing import Optional


@dataclass
class ArticleAppInputDTO:
    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    libro_o_titulo: Optional[str] = None


@dataclass
class ArticleAppOutputDTO:
    id: int
    materia_juridica: str
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    archivo_json_url: str
    libro_o_titulo: Optional[str] = None
    similitud: Optional[float] = None


@dataclass
class DeleteFileAppInputDTO:
    archivo_json_url: str
