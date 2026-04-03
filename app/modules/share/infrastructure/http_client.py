import logging
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from charset_normalizer import from_bytes

from app.core.config import settings
from app.modules.legal_library.domain.services.document_downloader import (
    DocumentDownloader,
)
from app.modules.share.exceptions.http_exceptions import (
    DisallowedDomainError,
    HTTPDownloadError,
)

logger = logging.getLogger("app.share.infrastructure.http_client")


class HTTPClient(DocumentDownloader):
    def __init__(self, allowed_domains: Optional[List[str]] = None):
        self.allowed_domains = allowed_domains or settings.ALLOWED_DOMAINS
        self._ssl_fallback_warned_domains: set[str] = set()

    def _validate_domain(self, url: str):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain not in self.allowed_domains:
            logger.warning(f"Intento de acceso a dominio no permitido: {domain}")
            raise DisallowedDomainError(domain)

    def _is_ssl_verification_error(self, error: Exception) -> bool:
        error_text = str(error).lower()
        return (
            "certificate_verify_failed" in error_text
            or "unable to get local issuer certificate" in error_text
            or "ssl" in error_text
            and "verify" in error_text
        )

    async def _request_with_ssl_fallback(self, method: str, url: str) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, verify=settings.HTTP_VERIFY_SSL
            ) as client:
                return await client.request(method, url)
        except httpx.TransportError as e:
            can_retry_insecure = (
                settings.HTTP_VERIFY_SSL
                and settings.HTTP_ALLOW_INSECURE_SSL_FALLBACK
                and self._is_ssl_verification_error(e)
            )

            if not can_retry_insecure:
                raise

            domain = urlparse(url).netloc
            if domain not in self._ssl_fallback_warned_domains:
                self._ssl_fallback_warned_domains.add(domain)
                logger.warning(
                    "SSL verification failed for %s; retrying with verify=False due to HTTP_ALLOW_INSECURE_SSL_FALLBACK",
                    domain,
                )

            async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
                return await client.request(method, url)

    async def fetch_content(self, url: str) -> str:
        """Descarga el contenido de una URL después de validar el dominio."""
        self._validate_domain(url)

        try:
            response = await self._request_with_ssl_fallback("GET", url)
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

    async def head_content_length(self, url: str) -> Optional[int]:
        """Obtiene Content-Length de forma segura. Si no está disponible, retorna None."""
        self._validate_domain(url)

        try:
            response = await self._request_with_ssl_fallback("HEAD", url)
            response.raise_for_status()

            length = response.headers.get("Content-Length") or response.headers.get(
                "content-length"
            )
            if not length:
                return None

            try:
                parsed = int(length)
                return parsed if parsed > 0 else None
            except ValueError:
                return None
        except Exception as e:
            logger.debug(f"No se pudo obtener Content-Length para {url}: {e}")
            return None
