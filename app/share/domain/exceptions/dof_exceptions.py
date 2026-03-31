from app.share.exceptions.base_exceptions import DomainException


class InvalidDOFDocumentError(DomainException):
    def __init__(
        self,
        detail: str = "El documento no parece ser un formato válido del Diario Oficial de la Federación (DOF).",
    ):
        super().__init__(message=detail, code="INVALID_DOF_DOCUMENT", status_code=422)


class ParsingError(DomainException):
    def __init__(self, message: str):
        super().__init__(
            message=f"Error durante el parseo del documento: {message}",
            code="PARSING_ERROR",
            status_code=422,
        )
