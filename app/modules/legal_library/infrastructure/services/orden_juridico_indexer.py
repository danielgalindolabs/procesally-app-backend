import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.modules.legal_library.domain.services.legal_indexer import LegalIndexer

logger = logging.getLogger("app.legal_library.infrastructure.orden_juridico_indexer")


class OrdenJuridicoIndexer(LegalIndexer):
    """
    Implementación del indexador para el sitio ordenjuridico.gob.mx.
    Busca enlaces que sigan el patrón 'woXXXXX.html'.
    """

    def __init__(self):
        # Patrón para detectar los documentos federales según la estructura conocida
        self.doc_pattern = re.compile(r"wo\d+\.html$", re.IGNORECASE)

    def discover_links(self, html_content: str, base_url: str) -> dict[str, str]:
        discovered = {}
        soup = BeautifulSoup(html_content, "html.parser")

        # Buscar todos los tags <a>
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]

            # Verificar si el enlace coincide con el patrón esperado
            if self.doc_pattern.search(href):
                # Construir la URL absoluta
                absolute_url = urljoin(base_url, href)

                # Intentar extraer un título limpio
                raw_text = a_tag.get_text(strip=True)
                # Si no hay texto, intentar usar el atributo title o el propio href
                title = raw_text or a_tag.get("title") or href.split("/")[-1]

                # Limpiar el título de saltos de línea extra y espacios continuos
                title = re.sub(r"\s+", " ", title).strip()

                if title and absolute_url:
                    # Guardamos la URL (si hay títulos duplicados, se sobreescribe con el último)
                    # En un caso más complejo, podríamos agregar un sufijo, pero para índices suele bastar
                    discovered[title] = absolute_url

        logger.info(f"Se encontraron {len(discovered)} documentos en el índice.")
        return discovered
