import logging
from urllib.parse import urlparse

import httpx
from charset_normalizer import from_bytes

from app.core.config import settings
from app.modules.legal_library.domain.services.document_downloader import \
    DocumentDownloader
from app.share.exceptions.http_exceptions import (DisallowedDomainError,
                                                  HTTPDownloadError)

logger = logging.getLogger("app.share.infrastructure.http_client")


class HTTPClient(DocumentDownloader):
    """Cliente HTTP con validación de dominios permitidos."""

    def __init__(self, allowed_domains: list[str] | None = None):
        self.allowed_domains = allowed_domains or settings.ALLOWED_DOMAINS

    def _validate_domain(self, url: str):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain not in self.allowed_domains:
            logger.warning(f"Intento de acceso a dominio no permitido: {domain}")
            raise DisallowedDomainError(domain)

    async def fetch_content(self, url: str) -> str:
        """Descarga el contenido de una URL después de validar el dominio."""
        self._validate_domain(url)

        async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()

                # Usamos charset-normalizer para una decodificación robusta (especialmente para sitios con Windows-1252/ISO-8859-1)
                # que no especifican correctamente el charset en los headers.
                decoded = from_bytes(response.content).best()
                if decoded and decoded.encoding:
                    logger.info(
                        f"Decodificando {url} usando {decoded.encoding} (coherencia: {decoded.coherence})"
                    )
                    return str(decoded)

                return response.text
            except httpx.HTTPStatusError as e:
                logger.error(f"Error HTTP al descargar {url}: {e.response.status_code}")
                raise HTTPDownloadError(url=url, status_code=e.response.status_code)
            except Exception as e:
                logger.error(f"Error inesperado al descargar {url}: {e}")
                raise
