from abc import ABC, abstractmethod
from typing import Optional


class DocumentDownloader(ABC):
    """Interfaz para descargar documentos legales."""

    @abstractmethod
    async def fetch_content(self, url: str) -> str:
        """Descarga el contenido de una URL y lo devuelve como texto."""
        pass

    @abstractmethod
    async def head_content_length(self, url: str) -> Optional[int]:
        """Obtiene el tamaño del recurso remoto (bytes) cuando esté disponible."""
        pass
