from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedArticle:
    """Estructura pura que representa un artículo extraído de cualquier documento legal."""

    materia_juridica: List[str]
    ley_o_codigo: str
    numero_articulo: str
    cuerpo_texto: str
    libro_o_titulo: Optional[str] = None


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, content: str) -> List[ParsedArticle]:
        """Parsea un documento legal y devuelve una lista de artículos extraídos."""
        pass
