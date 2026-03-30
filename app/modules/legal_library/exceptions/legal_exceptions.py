from app.share.exceptions.base_exceptions import DomainException


class ArticleNotFoundError(DomainException):
    def __init__(self, article_id: int):
        super().__init__(
            message=f"El artículo con ID {article_id} no fue encontrado.",
            code="ARTICLE_NOT_FOUND",
            status_code=404,
        )


class DuplicateArticleError(DomainException):
    def __init__(self, numero_articulo: str, ley: str):
        super().__init__(
            message=f"El artículo '{numero_articulo}' de la ley '{ley}' ya existe en la biblioteca.",
            code="DUPLICATE_ARTICLE",
            status_code=409,
        )
