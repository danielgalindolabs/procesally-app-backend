from abc import ABC, abstractmethod


class LegalIndexer(ABC):
    """Interfaz para descubrir enlaces a leyes desde una página índice."""

    @abstractmethod
    def discover_links(self, html_content: str, base_url: str) -> dict[str, str]:
        """
        Analiza el contenido HTML de una página índice y extrae los enlaces
        a los documentos legales individuales.

        Debe retornar un diccionario donde:
        - key: Título de la ley o documento (texto del enlace o inferido).
        - value: URL absoluta al documento.
        """
        pass
