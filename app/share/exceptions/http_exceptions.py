from app.share.exceptions.base_exceptions import InfrastructureException


class DisallowedDomainError(InfrastructureException):
    """Excepción lanzada cuando se intenta acceder a un dominio no permitido."""

    def __init__(self, domain: str):
        super().__init__(
            message=f"El dominio '{domain}' no está en la lista de dominios permitidos.",
            code="DISALLOWED_DOMAIN",
        )


class HTTPDownloadError(InfrastructureException):
    """Excepción lanzada cuando la descarga de un documento falla por status de red."""

    def __init__(self, url: str, status_code: int):
        super().__init__(
            message=f"Error {status_code} al intentar descargar: {url}",
            code="DOWNLOAD_ERROR",
        )
