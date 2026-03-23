class AppBaseException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class DomainException(AppBaseException):
    def __init__(self, message: str, code: str = "DOMAIN_ERROR", status_code: int = 400):
        super().__init__(message, code, status_code)

class InfrastructureException(AppBaseException):
    def __init__(self, message: str, code: str = "INFRASTRUCTURE_ERROR", status_code: int = 502):
        super().__init__(message, code, status_code)
