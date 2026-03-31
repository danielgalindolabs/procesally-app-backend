from abc import ABC, abstractmethod


class DocumentDownloader(ABC):
    """Interfaz para descargar documentos legales."""

    @abstractmethod
    async def fetch_content(self, url: str) -> str:
        """Descarga el contenido de una URL y lo devuelve como texto."""
        pass
